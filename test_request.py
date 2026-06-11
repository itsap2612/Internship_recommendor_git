# import requests

# url = "http://127.0.0.1:5000/recommend"
# payload = {
#     "resume": "I know Python, Flask, SQL and Git.",
#     "location": "India"
# }

# response = requests.post(url, json=payload)

# print("Status Code:", response.status_code)
# print("Response:", response.json())
import requests

url = "http://127.0.0.1:5000/create-profile"
payload = {
    "name": "Astitva",
    "skills": "Python, Java, C++",
    "interests": "Machine Learning, Data Science"
}

response = requests.post(url, json=payload)

print("Status Code:", response.status_code)
print("Response:", response.json())