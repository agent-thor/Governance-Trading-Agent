import os
import pandas as pd
from datetime import datetime
import logging
from dotenv import load_dotenv

# Import required modules
from proposal_revamp.models.sentiment import SentimentPredictor
from proposal_revamp.models.reasoning import Reasoning
from proposal_revamp.models.summarization import Summarization
from proposal_revamp.models.price_prediction import RobertaForRegressionBullish, RobertaForRegressionBearish
from proposal_revamp.core.trade_logic import TradeLogic
from proposal_revamp.exchange.binance_futures import BinanceAPI
from proposal_revamp.services.notification import send_slack_message

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize models and components
        logger.info("Initializing models and components...")
        sentiment_predictor = SentimentPredictor()
        reasoning = Reasoning()
        summarizer = Summarization()
        bullish_predictor = RobertaForRegressionBullish()
        bearish_predictor = RobertaForRegressionBearish()
        trade_logic = TradeLogic()
        binance_api = BinanceAPI()

        # Example proposal data (hardcoded for demonstration)
        new_row_df = {
            "post_id": "pankcakeswap--5073a43409eb1f697712c9148a7a59f3e3304c7ae2cd09727dd9f1290eba85f6",
            "coin": "pankcakeswap",
            "description": "The market is going up and seems bullish",
            "discussion_link": "https:google.com",
            "timestamp": "2023-09-11"
        }
        new_row_df = pd.DataFrame([new_row_df])

        # Process each new proposal
        for _, row in new_row_df.iterrows():
            logger.info(f"Processing proposal for {row['coin']}")
            
            # Get proposal summary
            summary = summarizer.get_summary(row['description'])
            logger.info(f"Generated summary: {summary}")

            # Analyze sentiment
            sentiment_score = sentiment_predictor.predict(summary)
            logger.info(f"Sentiment score: {sentiment_score}")

            # Get reasoning about the proposal
            reasoning_result = reasoning.get_reasoning(summary)
            logger.info(f"Reasoning result: {reasoning_result}")

            # Combine sentiment analysis results
            final_sentiment = sentiment_predictor.get_final_sentiment(
                sentiment_score,
                reasoning_result
            )
            logger.info(f"Final sentiment: {final_sentiment}")

            # Check if text is genuine (simplified for example)
            is_genuine = True

            if is_genuine:
                # Trigger trade based on sentiment
                if final_sentiment['sentiment'] == 'positive' and final_sentiment['score'] >= 0.80:
                    logger.info("Positive sentiment detected, predicting price movement...")
                    price_prediction = bullish_predictor.predict(summary)
                    trade_logic.trigger_trade(
                        row['coin'],
                        'long',
                        price_prediction,
                        binance_api
                    )
                    
                elif final_sentiment['sentiment'] == 'negative' and final_sentiment['score'] >= 0.80:
                    logger.info("Negative sentiment detected, predicting price movement...")
                    price_prediction = bearish_predictor.predict(summary)
                    trade_logic.trigger_trade(
                        row['coin'],
                        'short',
                        price_prediction,
                        binance_api
                    )
                else:
                    logger.info("Sentiment score below threshold or neutral, no trade triggered")
            else:
                logger.warning("Text classified as non-genuine, skipping trade")

            # Send notification
            notification_msg = f"Processed proposal for {row['coin']}\nSentiment: {final_sentiment['sentiment']}\nScore: {final_sentiment['score']}"
            send_slack_message(notification_msg)

    except Exception as e:
        logger.error(f"Error in main process: {str(e)}", exc_info=True)
        send_slack_message(f"Error in trading bot: {str(e)}")

if __name__ == "__main__":
    main() 