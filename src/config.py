# -*- coding: utf-8 -*-

"""
Configuration management for the AI CLI tool.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """
    Configuration manager for the AI CLI tool.
    """
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()
    
    def _get_config_dir(self) -> Path:
        """
        Get the configuration directory, creating it if it doesn't exist.
        
        Returns:
            Path object for the configuration directory
        """
        # Use XDG_CONFIG_HOME if available, otherwise use ~/.config
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            config_dir = Path(config_home) / "ai-cli"
        else:
            config_dir = Path.home() / ".config" / "ai-cli"
            
        # Create the directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        return config_dir
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the configuration from the config file.
        
        Returns:
            Dictionary containing the configuration
        """
        if not self.config_file.exists():
            return {
                "api_key": None,
                "model": "deepseek-chat",  # Default to v3 model as per requirements
                "history_size": 10,
            }
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"Warning: Failed to load config from {self.config_file}, using defaults")
            return {
                "api_key": None,
                "model": "deepseek-chat",
                "history_size": 10,
            }
    
    def save_config(self):
        """Save the configuration to the config file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save config to {self.config_file}: {e}")
    
    def get_api_key(self) -> Optional[str]:
        """
        Get the API key.
        
        Returns:
            The API key, or None if not configured
        """
        # First check environment variable
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if api_key:
            return api_key
            
        # Then check config file
        return self.config.get("api_key")
    
    def get_model(self) -> str:
        """
        Get the model name.
        
        Returns:
            The model name
        """
        return self.config.get("model", "deepseek-chat")
    
    def set_api_key(self, api_key: str):
        """
        Set the API key.
        
        Args:
            api_key: The API key to set
        """
        self.config["api_key"] = api_key
        self.save_config()
    
    def set_model(self, model: str):
        """
        Set the model name.
        
        Args:
            model: The model name to set
        """
        self.config["model"] = model
        self.save_config()
    
    def interactive_setup(self):
        """Run an interactive setup to configure API key and other settings."""
        print("AI CLI Configuration")
        print("====================")
        print()
        
        # API key setup
        current_key = self.get_api_key()
        if current_key:
            # Mask the API key for display
            masked_key = current_key[:4] + "*" * (len(current_key) - 8) + current_key[-4:]
            print(f"Current API key: {masked_key}")
            change_key = input("Change API key? [y/N] ").lower() == "y"
        else:
            print("No API key configured.")
            change_key = True
        
        if change_key:
            api_key = input("Enter your DeepSeek API key: ").strip()
            if api_key:
                self.set_api_key(api_key)
                print("API key saved.")
            else:
                print("API key not changed.")
        
        # Model setup
        current_model = self.get_model()
        print(f"\nCurrent model: {current_model}")
        change_model = input("Change model? [y/N] ").lower() == "y"
        
        if change_model:
            print("\nAvailable models:")
            print("  1. deepseek-chat (default)")
            print("  2. deepseek-coder")
            print("  3. Other (specify)")
            
            choice = input("\nSelect model (1-3): ").strip()
            if choice == "1":
                self.set_model("deepseek-chat")
            elif choice == "2":
                self.set_model("deepseek-coder")
            elif choice == "3":
                model = input("Enter model name: ").strip()
                if model:
                    self.set_model(model)
                else:
                    print("Model not changed.")
            else:
                print("Invalid choice, model not changed.")
        
        print("\nConfiguration complete.")
        
        # Environment variable suggestion
        print("\nTip: You can also set the API key using the DEEPSEEK_API_KEY environment variable:")
        if os.name == "posix":  # Linux/macOS
            print('  export DEEPSEEK_API_KEY="your-api-key-here"')
        else:  # Windows
            print('  set DEEPSEEK_API_KEY=your-api-key-here')
