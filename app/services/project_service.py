from nanoid import generate

def generate_project_nanoid() -> str:
    return generate(size=12)
