import torch
from transformers import RobertaTokenizer, RobertaModel,RobertaConfig
from safetensors.torch import load_file

class RobertaRegressionPredictor(torch.nn.Module):
    def __init__(self, model_name='roberta-base'):
        super(RobertaRegressionPredictor, self).__init__()
        # Load the RoBERTa model and add a regression head
        self.roberta = RobertaModel.from_pretrained(model_name)
        self.regressor = torch.nn.Linear(self.roberta.config.hidden_size, 1)

    def forward(self, input_ids, attention_mask=None, labels=None):
        # Forward pass through the RoBERTa model
        outputs = self.roberta(input_ids, attention_mask=attention_mask)
        logits = self.regressor(outputs.pooler_output)  # Use the pooled output for regression
        loss = None
        if labels is not None:
            # Calculate Mean Absolute Error (MAE) loss for regression
            loss = torch.nn.functional.l1_loss(logits.squeeze(), labels)
        return {'loss': loss, 'logits': logits} if loss is not None else {'logits': logits}

class RobertaForRegressionBearish:
    def __init__(self, model_path):
        # Set device to CUDA if available, otherwise CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Load the tokenizer
        self.tokenizer = RobertaTokenizer.from_pretrained("roberta-base")
        
        # Initialize the custom regression model
        self.model = RobertaRegressionPredictor()
        # Load model weights from the safetensors file
        state_dict = load_file(f"{model_path}/model.safetensors", device=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()
        
    def predict(self, texts):
        # Ensure input is a list of texts
        if isinstance(texts, str):
            texts = [texts]

        # Tokenize and prepare inputs
        encodings = self.tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=128,
            return_tensors='pt'
        )
        encodings = {key: val.to(self.device) for key, val in encodings.items()}
        
        # Predict continuous values
        with torch.no_grad():
            outputs = self.model(**encodings)
            predictions = outputs['logits'].squeeze(-1).cpu().numpy()
        
        # Return predictions as a list of floats
        return predictions.tolist()