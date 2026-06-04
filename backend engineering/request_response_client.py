import requests


def fetch_user(user_id: int) -> dict | None:
    url = f"https://jsonplaceholder.typicode.com/users/{user_id}"
    response = requests.get(url, timeout=5)

    if response.status_code == 200:
        return response.json()

    print(f"Request failed with status code: {response.status_code}")
    return None


if __name__ == "__main__":
    user = fetch_user(1)

    if user is not None:
        print(f"User name: {user['name']}")
        print(f"Email: {user['email']}")
