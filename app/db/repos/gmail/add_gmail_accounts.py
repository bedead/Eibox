from typing import List
from app.schemas.google_access_token import GoogleAccessTokens
from app.schemas.gmail_account import GmailAccount
from app.db.redis import db_store


def add_gmail_account(token: GoogleAccessTokens, namespace_for_memory: str):

    username = token.username
    key = f"user-gmail-accounts:{username}"

    # get all the gmail accounts object data from db
    gmail_accounts: List[GmailAccount] = db_store.get(
        namespace=namespace_for_memory, key=key
    )

    # format current gmail account data to object
    gaccount = GmailAccount(
        email=token.account_email,
        refresh_token=token.token["refreshToken"],
        access_token=token.token["accessToken"],
        expires_in=token.token["expiresIn"],
        token_type=token.token["tokenType"],
        scope=token.token["scope"],
    )

    # add the new account data object
    gmail_accounts.append(gaccount)

    # call save_gmail_account to save the new updated gmail accounts data
