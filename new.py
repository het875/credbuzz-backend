import requests

def send_otp(mobile):
    url = "https://control.msg91.com/api/v5/otp"
    payload = {
        "mobile": mobile,  # Must include country code, e.g., "91XXXXXXXXXX"
        "template_id": "693c333d63d3635f1f085b14",  # Your MSG91 template ID
        "authkey": "482694AvTHENVi693c31d6P1"
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Example usage
mobile_number = "919099421188"  # include country code
send_response = send_otp(mobile_number)
print(send_response)


def verify_otp(mobile, otp):
    url = "https://control.msg91.com/api/v5/otp/verify"
    payload = {
        "mobile": mobile,
        "otp": otp,  # OTP received on your phone
        "authkey": "482694AvTHENVi693c31d6P1"
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Example usage
user_otp = input("Enter OTP you received: ")
verify_response = verify_otp(mobile_number, user_otp)
print(verify_response)
