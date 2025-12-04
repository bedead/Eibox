# tests/test_remove_gmail_account_unittest.py

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.services.data_ops.gmail.accounts.remove_gmail_accounts import (
    remove_gmail_account,
)


class TestRemoveGmailAccount(unittest.TestCase):

    @patch(
        "app.services.data_ops.auth.get_user_data"
    )
    @patch("app.services.data_ops.gmail.accounts.get_gmail_accounts")
    def test_remove_gmail_account_success(
        self, mock_get_user_data, mock_get_gmail_account
    ):
        # Mock return values
        mock_get_user_data.return_value = {"username": "testuser"}
        mock_get_gmail_account.return_value = {"accounts": ["test@gmail.com"]}

        response = remove_gmail_account(
            username="satyam",
            namespace_for_memory=("auth", "user"),
            email_address="satyammishra9050@gmail.com",
        )

        self.assertEqual(response, {"success": True})
        mock_get_user_data.assert_called_once()
        mock_get_gmail_account.assert_called_once()

    @patch(
        "app.services.data_ops.gmail.accounts.remove_gmail_account.get_gmail_account"
    )
    @patch("app.services.data_ops.gmail.accounts.remove_gmail_account.get_user_data")
    def test_remove_gmail_account_error(
        self, mock_get_user_data, mock_get_gmail_account
    ):
        # Make one of the dependencies throw an error
        mock_get_user_data.side_effect = Exception("DB failure")

        with self.assertRaises(HTTPException) as ctx:
            remove_gmail_account(
                username="satyam",
                namespace_for_memory=("auth", "user"),
                email_address="satyammishra9050@gmail.com",
            )

        self.assertEqual(ctx.exception.status_code, 500)
        self.assertIn("DB failure", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
