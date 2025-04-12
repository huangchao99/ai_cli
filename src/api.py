# -*- coding: utf-8 -*-

"""
DeepSeek API client implementation
"""

import os
import json
import requests
from typing import Dict, Any, Iterator, Optional


class DeepSeekClient:
    """
    Client for interacting with the DeepSeek API.
    """
    
    API_BASE_URL = "https://api.deepseek.com/v1"  # Assuming v1 for DeepSeek API
    DEFAULT_MODEL = "deepseek-chat"   # Default to v3 model as specified in requirements
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Initialize the DeepSeek API client.
        
        Args:
            api_key: DeepSeek API key
            model: Model identifier to use (defaults to DEFAULT_MODEL)
        """
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL
        
    def _get_headers(self) -> Dict[str, str]:
        """
        Get the headers required for API requests.
        
        Returns:
            Dict containing headers for API requests
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def generate(self, prompt: str) -> str:
        """
        Generate a completion for the given prompt.
        
        Args:
            prompt: The input prompt
            
        Returns:
            The generated text response
        
        Raises:
            Exception: If the API request fails
        """
        url = f"{self.API_BASE_URL}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        response = requests.post(
            url, 
            headers=self._get_headers(), 
            json=payload,
        )
        
        if response.status_code != 200:
            error_info = response.json() if response.content else {"error": "Unknown error"}
            raise Exception(f"API request failed with status {response.status_code}: {error_info}")
            
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def generate_stream(self, prompt: str) -> Iterator[str]:
        """
        Generate a streaming completion for the given prompt.
        
        Args:
            prompt: The input prompt
            
        Yields:
            Chunks of the generated text as they become available
            
        Raises:
            Exception: If the API request fails
        """
        url = f"{self.API_BASE_URL}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        
        response = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            stream=True,
        )
        
        if response.status_code != 200:
            error_info = response.json() if response.content else {"error": "Unknown error"}
            raise Exception(f"API request failed with status {response.status_code}: {error_info}")
            
        # Process the streaming response
        for line in response.iter_lines():
            if line:
                # Skip the "data: " prefix and empty lines
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    line = line[6:]
                    
                    # The end of the stream is marked with [DONE]
                    if line == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(line)
                        delta = data["choices"][0]["delta"]
                        if "content" in delta and delta["content"]:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Retrieve the current account balance and usage information.
        
        Returns:
            Dictionary containing balance and usage information
            
        Raises:
            Exception: If the API request fails
        """
        # 正确的余额查询端点 (直接使用base URL的根域名)
        url = "https://api.deepseek.com/user/balance"
        
        try:
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            response = requests.get(
                url,
                headers=headers
            )
            
            if response.status_code != 200:
                error_info = response.json() if response.content else {"error": "Unknown error"}
                raise Exception(f"API错误 (状态码 {response.status_code}): {error_info}")
            
            # 解析并返回实际的余额信息
            return response.json()
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络连接错误: {e}")
    
    def generate_diff(self, original_content: str, prompt: str, input_text: Optional[str] = None) -> str:
        """
        Generate a diff-style modification of the original content.
        
        Args:
            original_content: The original file content
            prompt: The instruction for modification
            input_text: Optional additional context
            
        Returns:
            A unified diff format string showing suggested changes
            
        Raises:
            Exception: If the API request fails
        """
        # Construct a prompt that instructs the model to provide a diff
        system_message = (
            "You are an expert programmer helping to modify code or text. "
            "Analyze the given content and suggest specific improvements based on the user's instructions. "
            "IMPORTANT: Your response MUST be in a proper unified diff format as follows:\n\n"
            "```diff\n"
            "--- original\n"
            "+++ modified\n"
            "@@ -line_number,number_of_lines +line_number,number_of_lines @@\n"
            " unchanged line\n"
            "-removed line\n"
            "+added line\n"
            " unchanged line\n"
            "```\n\n"
            "Guidelines:\n"
            "1. Include @@ line indicators with proper line numbers\n"
            "2. Include a few lines of context before and after changes\n"
            "3. Mark removed lines with '-' and added lines with '+'\n"
            "4. Unchanged context lines start with a space\n"
            "5. Provide meaningful improvements addressing the prompt\n"
            "6. Only respond with the diff format - no explanations before or after"
        )
        
        user_message = f"{prompt}\n\n"
        if input_text and input_text != original_content:
            user_message += f"Context:\n{input_text}\n\n"
        user_message += f"Content to modify:\n```\n{original_content}\n```"
        
        url = f"{self.API_BASE_URL}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.2,  # Lower temperature for more focused output
        }
        
        response = requests.post(
            url, 
            headers=self._get_headers(), 
            json=payload,
        )
        
        if response.status_code != 200:
            error_info = response.json() if response.content else {"error": "Unknown error"}
            raise Exception(f"API request failed with status {response.status_code}: {error_info}")
            
        result = response.json()
        return result["choices"][0]["message"]["content"]
