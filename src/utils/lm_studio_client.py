"""
LM Studio client for interacting with local LLM models.

This module provides a client for communicating with LM Studio's API endpoints 
following the official documentation at https://lmstudio.ai/docs/python
"""

import json
import logging
import requests
from typing import Dict, List, Union, Optional, Any

# Configure logger
logger = logging.getLogger(__name__)

class LMStudioClient:
    """Client for interacting with LM Studio's API endpoints."""
    
    def __init__(self, api_base: str = "http://localhost:1234"):
        """
        Initialize the LM Studio client.
        
        Args:
            api_base (str): Base URL for the LM Studio API
        """
        self.api_base = api_base.rstrip('/')
        self.session = requests.Session()
        logger.debug(f"LM Studio client initialized with API base: {self.api_base}")
    
    def list_models(self) -> List[Dict]:
        """
        List all available models in LM Studio.
        
        Returns:
            List[Dict]: List of model information dictionaries
        """
        try:
            response = self.session.get(f"{self.api_base}/api/v1/models")
            response.raise_for_status()
            models = response.json()
            logger.debug(f"Retrieved {len(models)} models from LM Studio")
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            return []
    
    def generate(self, 
                prompt: str, 
                model: str = "default", 
                temperature: float = 0.7,
                max_tokens: int = 2048,
                stop: Optional[List[str]] = None) -> Optional[str]:
        """
        Generate text from a prompt using LM Studio.
        
        Args:
            prompt (str): The prompt text
            model (str): Model to use for generation (or "default")
            temperature (float): Sampling temperature
            max_tokens (int): Maximum tokens to generate
            stop (List[str], optional): Stop sequences
            
        Returns:
            Optional[str]: Generated text or None if failed
        """
        try:
            payload = {
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            if model != "default":
                payload["model"] = model
                
            if stop:
                payload["stop"] = stop
            
            response = self.session.post(
                f"{self.api_base}/api/v1/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            if "content" in result:
                return result["content"]
            else:
                logger.warning("Completion response did not contain 'content' field")
                return None
        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}")
            return None
    
    def generate_chat(self,
                     messages: List[Dict[str, str]],
                     model: str = "default",
                     temperature: float = 0.7,
                     max_tokens: int = 2048) -> Optional[str]:
        """
        Generate chat response from messages.
        
        Args:
            messages (List[Dict]): List of message dictionaries
            model (str): Model to use for generation (or "default")
            temperature (float): Sampling temperature
            max_tokens (int): Maximum tokens to generate
            
        Returns:
            Optional[str]: Generated response or None if failed
        """
        try:
            payload = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            if model != "default":
                payload["model"] = model
            
            response = self.session.post(
                f"{self.api_base}/api/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            return result.get("message", {}).get("content")
        except Exception as e:
            logger.error(f"Chat generation failed: {str(e)}")
            return None
    
    def get_embeddings(self, text: Union[str, List[str]], model: str = "default") -> Optional[List[List[float]]]:
        """
        Generate embeddings for text.
        
        Args:
            text (Union[str, List[str]]): Text or list of texts to embed
            model (str): Model to use for embeddings (or "default")
            
        Returns:
            Optional[List[List[float]]]: List of embeddings or None if failed
        """
        try:
            # Convert single string to list
            if isinstance(text, str):
                text = [text]
                
            payload = {
                "input": text
            }
            
            if model != "default":
                payload["model"] = model
            
            response = self.session.post(
                f"{self.api_base}/api/v1/embeddings",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            if "embeddings" in result:
                return result["embeddings"]
            
            logger.warning("Embeddings response did not contain 'embeddings' field")
            return None
        except Exception as e:
            logger.error(f"Embeddings generation failed: {str(e)}")
            return None

    def correct_text(self, 
                    text: str, 
                    prompt_template: str,
                    temperature: float = 0.1,
                    max_tokens: int = 4096) -> str:
        """
        Apply text correction using a prompt template.
        
        Args:
            text (str): Text to correct
            prompt_template (str): Prompt template with {input_text} placeholder
            temperature (float): Temperature for generation
            max_tokens (int): Maximum tokens to generate
            
        Returns:
            str: Corrected text or original if correction fails
        """
        if not text.strip():
            return text
            
        try:
            # Replace placeholder with actual text
            prompt = prompt_template.replace("{input_text}", text)
            
            # Use text generation for correction
            corrected = self.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return corrected or text
        except Exception as e:
            logger.error(f"Text correction failed: {str(e)}")
            return text