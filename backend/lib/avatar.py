
from importlib.resources import files
from dicebear import Avatar, Style

_style = Style.from_json(
    files("dicebear_styles").joinpath("initial-face.json").read_text("utf-8")
)

def get_avatar_svg(email: str, size: int = 200) -> str:
    """
    Generate a deterministic DiceBear 'initial-face' avatar SVG for a given email.

    Args:
        email: The user's email address (used as the seed, so the same
               email always produces the same avatar).
        size: Avatar size in pixels.

    Returns:
        SVG markup as a string.
    """
    normalized_email = email.strip().lower()

    avatar = Avatar(_style, {
        "seed": normalized_email,
        "size": size,
    })

    return avatar.to_data_uri()
