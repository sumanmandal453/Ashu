from app.core.credential_encryption import decrypt_credential


async def load_integration_credential(db, integration_id: str) -> str | None:
    """Load and decrypt a private integration credential."""

    rows = await db.select(
        "college_integration_secrets",
        query={"integration_id": f"eq.{integration_id}"},
        select="encrypted_credentials",
        limit=1,
    )

    if not rows:
        return None

    encrypted = rows[0].get("encrypted_credentials")

    if not encrypted:
        return None

    return decrypt_credential(encrypted)


async def delete_integration_credential(db, integration_id: str) -> None:
    """Delete a private integration credential."""

    await db.delete(
        "college_integration_secrets",
        query={"integration_id": f"eq.{integration_id}"},
    )
