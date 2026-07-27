from abc import ABC, abstractmethod


class LLMProvider(ABC):

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        ...
