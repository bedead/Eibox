from src.llm.workflow import get_ai_toolkit

ai_toolkit = get_ai_toolkit("groq")
email_data = {
    "id": "196850f189c355ef",
    "subject": "Old friend",
    "sender": "Satyam Mishra Personal1 <satyammishra9050@gmail.com>",
    "date": "Wed, 30 Apr 2025 10:27:46 +0530",
    "body": "Hey Satyam, how are you doing?\r\n",
    "unread": True,
    "snippet": "Hey Satyam, how are you doing?",
}


# print(ai_toolkit.generate_response("Hello, how are you?"))
print(ai_toolkit.chat_response("Hello, how are you?"))
print(ai_toolkit.chat_history)


# result = ai_toolkit.analyze_importance(email_data, json_output=True)
# print(result["output"])
# if result["output"].lower() == "yes":
#     print("The email is important.")
#     summary = ai_toolkit.summarize_email(email_data, json_output=True)
#     print("Summary:", summary["output"])

#     de1 = ai_toolkit.is_response_needed(email_data, json_output=True)
#     if de1["output"].lower() == "yes":
#         print("A response is needed.")
#         response_format = ai_toolkit.mail_response_format(email_data, json_output=True)
#         print("Response Format:", response_format["output"])

#         response = ai_toolkit.generate_response(
#             email_data, json_output=True, style=response_format["output"]
#         )
#         print("Generated Response:", response["output"])
#     else:
#         print("No response needed.")
# else:
#     print("The email is not important.")
