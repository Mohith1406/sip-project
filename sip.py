import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import pickle
import time
import bcrypt

# Helper function to get similar movies based on rating
def get_similar(movie_name, rating):
    # Calculate similarity ratings adjusted by the user's rating
    similar_ratings = corrMatrix[movie_name] * (rating - 2.5)
    # Sort the ratings in descending order
    similar_ratings = similar_ratings.sort_values(ascending=False)
    return similar_ratings

# Helper function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Define usernames, names, and passwords
usernames = ["user1", "user2"]
names = ["Alice Smith", "Bob Jones"]
emails = ["alice.smith@example.com", "bob.jones@example.com"]  # Add email field
passwords = ["password123", "securepass"]

# Hash the passwords using bcrypt
hashed_passwords = [hash_password(password) for password in passwords]

# Create the credentials dictionary
credentials = {
    "usernames": {
        usernames[i]: {
            "name": names[i],
            "email": emails[i],  # Add email field here
            "password": hashed_passwords[i]
        }
        for i in range(len(usernames))
    }
}


# Initialize the authenticator
authenticator = stauth.Authenticate(
    credentials,
    "movie_recommendation_app",
    "auth",
    cookie_expiry_days=30
)

# Login form with location parameter
auth_status = authenticator.login(location="main")

# Check if the authentication status is stored in session state
if 'authentication_status' in st.session_state:
    authentication_status = st.session_state['authentication_status']
    username = st.session_state['username'] if authentication_status else None
else:
    authentication_status = False
    username = None

# Main app content for authenticated users
if authentication_status:
    name = credentials["usernames"][username]["name"]
    st.write(f"Welcome, {name}!")

    # Load the precomputed correlation matrix from a Pickle file
    with open('corrMatrix.pkl', 'rb') as f:
        corrMatrix = pickle.load(f)

    # Extract movie titles from the correlation matrix
    movie_list = corrMatrix.columns.values

    # Streamlit app title
    st.title("Movie Recommendation System")

    # Initialize session state if it doesn't exist
    if 'selected_movies' not in st.session_state:
        st.session_state.selected_movies = []
    if 'ratings' not in st.session_state:
        st.session_state.ratings = []

    # Number of movies user wants to rate
    num_movies = st.number_input('How many movies do you want to rate?', min_value=1, max_value=20, step=1, value=3)

    # Dynamically generate selectbox fields for movie names and sliders for ratings
    for i in range(num_movies):
        # Ensure selected_movies and ratings lists are the correct length
        if len(st.session_state.selected_movies) <= i:
            st.session_state.selected_movies.append(movie_list[0])  # Default to the first movie
        if len(st.session_state.ratings) <= i:
            st.session_state.ratings.append(2.5)  # Default rating

        # Create a list of available movies excluding those already selected
        available_movies = [movie for movie in movie_list if movie not in st.session_state.selected_movies[:i]]

        # Determine the current movie selection
        current_selection = st.session_state.selected_movies[i]
        # Fallback to the first available movie if the current selection is not valid
        if current_selection not in available_movies:
            current_selection = available_movies[0]

        selected_movie = st.selectbox(
            f'Select Movie {i + 1}',
            available_movies,
            index=available_movies.index(current_selection),
            key=f"movie_select_{i}"
        )

        rating = st.slider(
            f'Rating for {selected_movie}',
            0.0, 5.0, st.session_state.ratings[i], step=0.5,
            key=f"rating_slider_{i}"
        )

        # Update session state
        st.session_state.selected_movies[i] = selected_movie
        st.session_state.ratings[i] = rating

    # When the user clicks the "Get Recommendations" button
    if st.button('Get Recommendations'):
        similar_movies_list = []
        with st.spinner('Generating recommendations...'):
            time.sleep(1.5)
            # Calculate similar movies for each rated movie
            for movie, rating in zip(st.session_state.selected_movies, st.session_state.ratings):
                if movie in corrMatrix.columns:
                    similar_movies_list.append(get_similar(movie, rating))
                else:
                    st.warning(f"Movie '{movie}' not found in the database.")

            if similar_movies_list:
                # Combine all the similar movies into a single DataFrame
                similar_movies = pd.concat(similar_movies_list, axis=1)

                # Sum across the rows to aggregate similar movie scores
                summed_similarities = similar_movies.sum(axis=1)

                # Sort the summed similarities in descending order and get the top 10 recommendations
                top_10_similar_movies = summed_similarities.sort_values(ascending=False)

                # Filter out the movies the user has already rated
                top_10_similar_movies = top_10_similar_movies[~top_10_similar_movies.index.isin(st.session_state.selected_movies)]
                top_10_similar_movies = top_10_similar_movies.head(10)

                # Create a list of top 10 recommended movie names
                recommended_movies = top_10_similar_movies.index.tolist()

                # Display the top 10 movie recommendations directly
                st.subheader("Top 10 Movie Recommendations")
                for i, movie in enumerate(recommended_movies, start=1):
                    st.write(f"{i}. {movie}")

        st.success('Recommendations generated!')

    # Logout button
    authenticator.logout("Logout", "sidebar")

elif authentication_status is False:
    st.error("Username/password is incorrect")
elif authentication_status is None:
    st.warning("Please enter your username and password")
