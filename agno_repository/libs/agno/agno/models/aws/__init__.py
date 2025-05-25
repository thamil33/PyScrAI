from agno_src.models.aws.bedrock import AwsBedrock

try:
    from agno_src.models.aws.claude import Claude
except ImportError:

    class Claude:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("`anthropic` not installed. Please install using `pip install anthropic`")


__all__ = [
    "AwsBedrock",
    "Claude",
]
