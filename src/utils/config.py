    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return {
            'api_key': os.getenv('LM_STUDIO_API_KEY'),  # Update API key if needed
            'model': os.getenv('LLM_MODEL', 'Meta-Llama-3.1-8B-Instruct-Q4_K_M'),  # Updated model name
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', self.get('llm.max.tokens', 1000))),
            'temperature': float(self.get('llm.temperature', 0.7))
        }