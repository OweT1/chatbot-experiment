from deepeval.test_case import ConversationalTestCase, LLMTestCase
# from deepeval.metrics import 

def convert_to_test_case(message_history: list[dict[str, str]]):
  starter_msg = message_history[0]["content"]
  remaining_conversation = message_history[1:]
  
  turns = []
  for i in range(0, len(remaining_conversation), 2):
    user_input = remaining_conversation[i]["content"]
    ai_output = remaining_conversation[i+1]["content"]
    curr_turn = LLMTestCase(
      input=user_input,
      actual_output=ai_output
    )
    turns.append(curr_turn)
  
  convo_test_case = ConversationalTestCase(
    chatbot_role=starter_msg,
    turns=turns
  )
  return convo_test_case
  