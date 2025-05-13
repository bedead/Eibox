from typing import List
import strip_markdown

from src.core.gmail.gmail_toolkit import GmailToolKit
from src.core.json.reader import JSONEmailReader
from src.core.llm.ai_toolkit import get_ai_toolkit
from src.core.utils._logs import setup_logging


from src.core.llm.providers.types.model_selector import ModelSelector
from src.core.llm.providers.types.providers import BaseProvider
from src.core.llm.providers.types.models_google import GoogleModel
from src.core.llm.providers.types.models_groq import GroqModel

# logger = logging.getLogger()
# logger.setLevel(logging.INFO)


def main():
    logger = setup_logging()
    logger.debug("Starting Mail Assistant application...")

    gmail_tool = GmailToolKit(interval=1, max_results=2)
    selected_model = ModelSelector(
        provider=BaseProvider.GOOGLE, model=GoogleModel.GEMINI_1_5_FLASH
    )
    ai_toolkit = get_ai_toolkit(model=selected_model)
    email_reader = JSONEmailReader()
    gmail_tool.start()

    while True:
        emails: List[dict] = email_reader.get_all_email_content()

        if not isinstance(emails, list) or not emails:
            # logger.debug("No emails found.")
            gmail_tool.resume()
            continue

        for i, mail_data in enumerate(emails):
            if not isinstance(mail_data, dict):
                logger.error(f"Invalid mail data format: {mail_data}")
                continue  # Skip this loop iteration

            logger.info(
                f"Processing email from {mail_data['sender']} - Subject: {mail_data['subject']} - {mail_data['date']}"
            )

            important_response = ai_toolkit.analyze_importance(
                email_data=mail_data, json_output=True
            )
            decision1 = important_response.get("output", "").lower().strip()

            logger.debug(f"is_mail_important output: {decision1}")

            if decision1 == "yes":
                logger.debug("Email identified as important.")

                summary = ai_toolkit.summarize_email(
                    email_data=mail_data, json_output=True
                )
                logger.info(f"AI: {summary['output']}")

                response_needed = ai_toolkit.is_response_needed(
                    email_data=mail_data, json_output=True
                )
                decision2 = response_needed.get("output", "").lower().strip()

                logger.debug(f"is_response_needed output: {decision2}")

                if decision2 == "yes":
                    logger.debug("Response required for this email.")

                    format_response = ai_toolkit.mail_response_format(
                        email_data=mail_data, json_output=True
                    )
                    response_format = format_response.get("output", "").lower().strip()

                    if response_format in ["proffessional", "formal"]:
                        logger.info(
                            f"Email format identified as '{response_format}'. Generating response..."
                        )
                        response_suggestion = ai_toolkit.generate_response(
                            email_data=mail_data,
                            json_output=True,
                            style=response_format,
                        )
                        RESPONSE_TXT: str = strip_markdown.strip_markdown(
                            response_suggestion["output"]
                        )
                        logger.info(f"AI: {RESPONSE_TXT}")

                        approve = input("Approve response? (y/n): ").strip().lower()
                        if approve == "y":
                            logger.info("Response approved. Sending...")
                            gmail_tool.send_response(
                                mail_data["sender"],
                                mail_data["subject"],
                                RESPONSE_TXT,
                            )
                        else:
                            enable_edit = (
                                input("Do you want to edit the response? (y/n): ")
                                .strip()
                                .lower()
                            )
                            if enable_edit == "y":
                                logger.info("Starting response editing...")
                                edited_response = input("Edit the response: ").strip()
                                gmail_tool.send_response(
                                    mail_data["sender"],
                                    mail_data["subject"],
                                    edited_response,
                                )
                            else:
                                logger.info("Response not approved. Skipping...")
                            logger.info("Response not approved. Skipping...")

                    else:
                        logger.debug(
                            f"Response format '{response_format}' not suitable for automated suggestion."
                        )
                else:
                    logger.info("No response required for this email.")
            else:
                logger.info(
                    f"Email from {mail_data['sender']} identified as not important. Skipping."
                )
                gmail_tool.resume()


if __name__ == "__main__":
    main()
