from pydantic import BaseModel


class OAuthCallbackRequest(BaseModel):
    oauth_token: str
    oauth_verifier: str
