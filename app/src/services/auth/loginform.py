from fastapi import Request
from typing import Optional, List

class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")

    async def is_valid(self):
        if not self.username or len(self.username) < 3:
            self.errors.append("The username must contain at least 3 characters")
        elif len(self.username) > 50:
            self.errors.append("The username must be no longer than 50 characters")
        if not self.password or len(self.password) == 0:
            self.errors.append("A valid password is required")
        if not self.errors:
            return True
        return False