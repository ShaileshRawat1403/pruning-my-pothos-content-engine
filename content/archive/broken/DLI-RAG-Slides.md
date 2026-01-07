# DLI-RAG-Slides

Building RAG Agents with LLMs
Introduction

1

Building RAG Agents with LLMs
Introduction

2

Large Language Models
Backbones for Language Understanding

Backbones for language tasks, including classification and generation.

https://www.nvidia.com/content/dam/en-zz/Solutions/lp/large-language-models-ebook/nvidia-llm-ebook-og.jpg

3

Dialog/Retrieval Agents
LLMs with Context and Control

User Asks 
Something

Agent 
Responds

https://www.nvidia.com/content/dam/en-zz/Solutions/lp/large-language-models-ebook/nvidia-llm-ebook-og.jpg

4

Dialog/Retrieval Agents
LLMs with Context and Control

LLM Orchestration: Software + LLM 
helps to route to software and LLMs.

User Asks 
Something

Agent 
Responds

https://www.nvidia.com/content/dam/en-zz/Solutions/lp/large-language-models-ebook/nvidia-llm-ebook-og.jpg

5

Dialog/Retrieval Agents
LLMs with Context and Control

LLM Orchestration: Software + LLM 
helps to route to software and LLMs.

User Asks 
Something

Agent 
Responds

Retrieval: Tool runs algorithms 
(database, code execution, 
semantic search, return a constant 
value, etc) to provide context

https://www.nvidia.com/content/dam/en-zz/Solutions/lp/large-language-models-ebook/nvidia-llm-ebook-og.jpg

6

Dialog/Retrieval Agents
LLMs with Context and Control

Retrieval: Tool runs algorithms 
(database, code execution, 
semantic search, return a constant 
value, etc) to provide context

Augmented: Based on tool 
responses, the software pipeline 
synthesizes some “context”
to feed to LLM w/ question.

LLM Orchestration: Software + LLM 
helps to route to software and LLMs.

User Asks 
Something

Agent 
Responds

https://www.nvidia.com/content/dam/en-zz/Solutions/lp/large-language-models-ebook/nvidia-llm-ebook-og.jpg

7

Dialog/Retrieval Agents
LLMs with Context and Control

LLM Orchestration: Software + LLM 
helps to route to software and LLMs.

User Asks 
Something

Agent 
Responds

Retrieval: Tool runs algorithms 
(database, code execution, 
semantic search, return a constant 
value, etc) to provide context

Augmented: Based on tool 
responses, the software pipeline 
synthesizes some “context”
to feed to LLM w/ question.

Generation: Based on question, 
instructions, and enhanced context, 
the LLM returns a response.

https://www.nvidia.com/content/dam/en-zz/Solutions/lp/large-language-models-ebook/nvidia-llm-ebook-og.jpg

8

Chat Applications
Full Applications Build with LLMs

https://www.nvidia.com/content/dam/en-zz/Solutions/lp/large-language-models-ebook/nvidia-llm-ebook-og.jpg

9

Chat Applications
Full Applications Build with LLMs

Production-Ready APIs That Run Anywhere | NVIDIA

10

Chat Applications
Full Applications Build with LLMs

Production-Ready APIs That Run Anywhere | NVIDIA

11

Prerequisites
RAG Agents in Production

• Prior LLM/LangChain Exposure

• Intermediate Python Experience

• Exposure to Web Engineering

12

12

Course Objectives
RAG Agents in Production

• Environment

• LLM Services

• Intro to LangChain (LCEL)

• Running State Chains

• Document Loading

• Embeddings

• Document Retrieval

• RAG Evaluation

13

13

Building RAG Agents with LLMs
Part 1: Your Course Environment

15

Typical Jupyter Labs Interface

jupyter lab . &; open -a Safari http://localhost:8888/lab 

16

Typical Jupyter Labs Interface

Web Browser

Your Device

Your Device

Python

C++

Files

OS

Hardware

jupyter lab . &; open -a Safari http://localhost:8888/lab 

17

Typical Jupyter Labs Interface

Web Browser

Your Device

Your Device

:8888

Python

C++

Jupyter 
Labs

Files

OS

Hardware

jupyter lab . &; open -a Safari http://localhost:8888/lab 

18

Typical Jupyter Labs Interface

Web Browser

Your Device

Your Device

:8888

Python

C++

Jupyter 
Labs

Files

OS

Hardware

jupyter lab . &; open -a Safari http://localhost:8888/lab 

https://colab.research.google.com

19

Typical Jupyter Labs Interface

Web Browser

Your Device

Your Device

:8888

Python

C++

Jupyter 
Labs

Files

OS

Hardware

Web Browser

Your Device

Files

OS

Hardware

Python

C++

jupyter lab . &; open -a Safari http://localhost:8888/lab 

https://colab.research.google.com

20

Typical Jupyter Labs Interface

Web Browser

Your Device

Your Device

:8888

Python

C++

Jupyter 
Labs

Files

OS

Hardware

Web Browser

Your Device

Files

OS

Hardware

Python

C++

jupyter lab . &; open -a Safari http://localhost:8888/lab 

https://colab.research.google.com

21

DLI Jupyter Labs Interface

22

DLI Jupyter Labs Interface

Remote Host

Your Device

Python

C++

Jupyter 
Labs

Files

OS

Hardware

Web Browser

Your Device
Your Device

23

DLI Jupyter Labs Interface

Remote Host

Good to go!
… sort of …
Your Device

Jupyter 
Labs

Python

C++

Files

OS

Hardware

Web Browser

Your Device
Your Device

24

DLI Jupyter Labs Interface

Remote Host

Data 
Loader

Shell

Scheduler

Env

Your Device

Jupyter 
Labs

Python

C++

Python

Node

Proxy 
Service

Files

OS

Hardware

Web Browser

Your Device
Your Device

More 
Processes?

25

DLI Jupyter Labs Interface

Remote Host

Data 
Loader

Shell

Scheduler

Env

Your Device

Jupyter 
Labs

Python

C++

Python

Node

Proxy 
Service

Files

OS

Hardware

Web Browser

Your Device
Your Device

More 
Processes?

Dividing 
Resources?

26

Containerization with Docker
Compartmentalizing Functionality Into Microservices

Host

Data 
Loader

Shell

Scheduler

Env

Your Device

Jupyter 
Labs

Python

C++

Python

Node

Proxy 
Service

Files

OS

Hardware

Host

:8070

Python

Sh

Volume

:8888

Your Device

:88

Volume

Jupyter

GPU/2

Python

C++

Files

OS

Hardware

27

Microservices Workflow

Web Browser

Your Device
Your Device

28

Microservices Workflow

Remote Host

Your Device

Python

C++

Files

OS

Hardware

1.Allocate Resources
2.Define Services
3.Construct Containers
4.Start Processes

Web Browser

Your Device
Your Device

29

Microservices Workflow

1.Allocate Resources
2.Define Services
3.Construct Containers
4.Start Processes

Remote Host

:8070

Python

Sh

Volume

:8888

Your Device

:88

Volume

Jupyter

GPU/2

Python

C++

Files

OS

Hardware

Web Browser

Your Device
Your Device

30

Microservices Workflow

1.Allocate Resources
2.Define Services
3.Construct Containers
4.Start Processes

Remote Host

Database 
Environment

:8070

:8888

Your Device

Data Loader

:88

Jupyter Notebook 
Environment

Python

C++

Files

OS

Hardware

Web Browser

Your Device
Your Device

31

Microservices Workflow

1.Allocate Resources
2.Define Services
3.Construct Containers
4.Start Processes

Remote Host

Database 
Environment

:8070

:8888

Your Device

Data Loader

:88

Jupyter Notebook 
Environment

Python

C++

Files

OS

Hardware

Web Browser

Your Device
Your Device

32

Company
Database

Web Browser

Your Device
Your Device

Scaling Containerized Applications

Arbitrary Host

Database 
Environment

:8070

:8888

Your Device

Data Loader

Jupyter Notebook 
Environment

Python

C++

Files

OS

Hardware

GenAI 
Service

Other 
Web 
Your Device
Browser
Devices

Other 
Web 
Your Device
Browser
Devices

Other 
Web 
Your Device
Browser
Devices

Other 
Web 
Your Device
Browser
Devices

33

Company
Database

Web Browser

Your Device
Your Device

Scaling Containerized Applications

Arbitrary Host

Database 
Environment

:8070

:8888

Your Device

Data Loader

Jupyter Notebook 
Environment

Python

C++

Files

OS

Hardware

GenAI 
Service

Other 
Web 
Your Device
Browser
Devices

Other 
Web 
Your Device
Browser
Devices

Other 
Web 
Your Device
Browser
Devices

Other 
Web 
Your Device
Browser
Devices

Your Device

Your Device

Your Device

34

Our Environment
Jupyter Notebooks

Remote Host

Your Device
Docker
Router

:88

Jupyter Notebook Server

35

35

Our Environment
Jupyter Notebooks + Frontend

:8090

Remote Host

Frontend

Your Device
Docker
Router

:88

Jupyter Notebook Server

36

36

Gradio

37

Simple Gradio ChatInterface

https://www.gradio.app/

https://huggingface.co/spaces/gradio/chatinterface_streaming_echo/blob/main/run.py

38

Gradio in HuggingFace Spaces

https://huggingface.co/spaces/camenduru-com/webui

39

Custom Gradio Block Interface

https://www.gradio.app/guides/creating-a-custom-chatbot-with-blocks

40

Our Environment
Jupyter Notebooks + Frontend

:8090

Remote Host

Frontend

Your Device
Docker
Router

:88

Jupyter Notebook Server

41

41

Building RAG Agents with LLMs
Part 2: LLM Services

42

Our Environment
Jupyter Notebooks + Frontend

:8090

Remote Host

Frontend

Your Device
Docker
Router

:88

Jupyter Notebook Server

43

43

Dialog/Retrieval Agents
LLMs with Context and Control

Execute with dialog management and information retrieval in production

https://www.nvidia.com/content/dam/en-zz/Solutions/lp/large-language-models-ebook/nvidia-llm-ebook-og.jpg

44

Dialog/Retrieval Agents
LLMs with Context and Control

Execute with dialog management and information retrieval in production

https://www.nvidia.com/content/dam/en-zz/Solutions/lp/large-language-models-ebook/nvidia-llm-ebook-og.jpg

45

Standalone Environment LLM

Remote Host

Frontend

Your Device
Docker
Router

Jupyter Notebook Server

46

Standalone Environment LLM

Remote Host

Frontend

Your Device
Docker
Router

Jupyter Notebook Server

LLM

47

Standalone Environment LLM

Jupyter Notebook 

Jupyter Notebook 

H200

A100

A10

4070

Jupyter Notebook 

VRAM-bound

CPU-only

<s>[INST]<<SYS>>
{{system_message}}
<</SYS>>

{{instruction}} [/INST] 
{{primer}}

<s>[INST]<<SYS>>
You are a code generator. 
Please provide Python code 
per the instruction.
<</SYS>>

Write a Fibonacci method [/INST] 
```python
## Implementation of Fibonacci w/

48

Standalone Environment LLM

Jupyter Notebook 

Jupyter Notebook 

H200

A100

A10

4070

Jupyter Notebook 

VRAM-bound

CPU-only

49

Standalone Environment LLM

Jupyter Notebook 

Jupyter Notebook 

H200

A100

A10

4070

Jupyter Notebook 

VRAM-bound

CPU-only

50

Remote LLM Access

Remote Host

Frontend

Your Device

Jupyter Notebook 

VRAM-bound

CPU-only

<s>[INST]<<SYS>>
{{system_message}}
<</SYS>>

{{instruction}} [/INST] 
{{primer}}

Llama

<s>[INST]<<SYS>>
You are a code generator. 
Please provide Python code 
per the instruction.
<</SYS>>

Write a Fibonacci method [/INST] 
```python
## Implementation of Fibonacci w/

51

Large Model Hosting Platforms

Remote Host

Frontend

Your Device

Jupyter Notebook 

VRAM-bound

CPU-only

NVIDIA 
GPU CLOUD

52

Large Model Hosting Platforms

NVIDIA 
GPU CLOUD

1.GPT4/3.5
2.Integrated Tools/Multimodal Support
3.Models/Query Router Internal
4.Path to Local Deployment Less Clear

1.Publicly Available Models
2.Models/Query Router Accessible
3.Path to Local Deployment/Self-Hosting
4.Pieces to Compose Complex Systems

53

Query Router Access

GPT4

Dalle-3

Embed

<s>[INST]<<SYS>>
{{system_message}}
<</SYS>>

{{instruction}}
[/INST] 
{{primer}}????

54

Query Router Access

{
"messages": [{

"content": "...",
"role": "system"

},{

"content": "...",
"role": "user"

}],
"model": ”gpt-4”,
"temperature": 0.2,
"top_p": 0.7,
"max_tokens": 1024,
"stream": True
}

/chat/completions

Facilitate

Monitor

Optimize

Load Balance

GPT4

Dalle-3

Embed

<s>[INST]<<SYS>>
{{system_message}}
<</SYS>>

{{instruction}}
[/INST] 
{{primer}}????

https://kubernetes.io/

55

Query Router Access

{
"messages": [{

"content": "...",
"role": "system"

},{

"content": "...",
"role": "user"

}],
"model": ”gpt-4”,
"temperature": 0.2,
"top_p": 0.7,
"max_tokens": 1024,
"stream": True
}

/chat/completions

Facilitate

Monitor

Optimize

Load Balance

GPT4

Dalle-3

Embed

<s>[INST]<<SYS>>
{{system_message}}
<</SYS>>

{{instruction}}
[/INST] 
{{primer}}????

https://kubernetes.io/

56

Large Model Hosting Platforms - OpenAI

OpenAI Gateway

GPT
(3.5/4)

embed-<>

Dalle-3

57

Large Model Hosting Platforms - OpenAI

Messages
Model Name
Settings
API Key

OpenAI Gateway

Responses

GPT
(3.5/4)

embed-<>

Dalle-3

58

Large Model Hosting Platforms - OpenAI

End-User Application

Retriever Microservice

Messages
Model Name
Settings
API Key

OpenAI Gateway

Responses

GPT
(3.5/4)

embed-<>

Dalle-3

Server Management

https://developer.nvidia.com/blog/simplifyin
g-ai-inference-in-production-with-triton/

59

Large Model Hosting Platforms

NVIDIA 
GPU CLOUD

1.GPT4/3.5
2.Integrated Tools/Multimodal Support
3.Models/Query Router Internal
4.Path to Local Deployment Less Clear

1.Publicly Available Models
2.Models/Query Router Accessible
3.Path to Local Deployment/Self-Hosting
4.Pieces to Compose Complex Systems

60

Large Model Hosting Platforms

NVIDIA 
GPU CLOUD

1.GPT4/3.5
2.Integrated Tools/Multimodal Support
3.Models/Query Router Internal
4.Path to Local Deployment Less Clear

1.Publicly Available Models
2.Models/Query Router Accessible
3.Path to Local Deployment/Self-Hosting
4.Pieces to Compose Complex Systems

61

{
"messages": [{

"content": "...",
"role": "system"

},{

"content": "...",
"role": "user"

}],
"model": ”mixtral”,
"temperature": 0.2,
"top_p": 0.7,
"max_tokens": 1024,
"stream": True
}

Query Router Access

GPT4

Dalle-3

Embed

<s>[INST]<<SYS>>
{{system_message}}
<</SYS>>

/chat/completions

{{instruction}} [/INST] 
{{primer}}

Mixtral

SDXL

Facilitate

Monitor

Optimize

Load Balance

“context”:{{context}}
“model”:“query”/”doc”

E5

{

}

https://kubernetes.io/

62

Full Deployment Stack

General 
Chatbot

Image 
Generator

Document
Copilot

Custom 
Server

NIMs

NeMo 
Retriever

Mixtral

E5

SDXL

RIVA

Video
Gen

TensorRT-LLM / vLLM

K8s

Azure
/AWS

Org
Cluster

https://developer.nvidia.com/blog/simplifyin
g-ai-inference-in-production-with-triton/

63

Our Environment
Jupyter Notebooks + Frontend
+ LLM Client

:8090

Remote Host

Frontend

LLMs

:9000

Your Device
Docker
Router

:88

Jupyter Notebook Server

64

64

NVIDIA Foundation Model Endpoints

NVIDIA 
GPU CLOUD

65

NVIDIA Foundation Model Endpoints

NVIDIA 
GPU CLOUD

66

NVIDIA Foundation Model Endpoints

NVIDIA 
GPU CLOUD

67

From Raw Requests to LangChain Model

69

From Raw Requests to LangChain Model

<s>[INST]<<SYS>>
{{system_message}}
<</SYS>>

> llm(“Hello world”)

ChatMessage(content=”hello”)

Query Router

{{instruction}} [/INST] 
{{primer}}

Llama

Mistral

> embedder(“Hello”)

[0.4535437, 0.0800435, ...]

Facilitate

Monitor

Optimize

“context”:{{context}}
“model”:“query”/”doc”

E5

{

}

70

LLM Interfaces
The Whole Stack

api.nvcf.
nvidia.com
/v2/nvcf

Scaled
Function 
Deployment 
Solution

71

71

LLM Interfaces
The Whole Stack

api.nvcf.
nvidia.com
/v2/nvcf

health.api.nvidia.com/
ai.api.nvidia.com/

integrate.api.nvidia.com

v1/models
v1/completions
v1/chat/completions
v1/embeddings

api.openai.com

v1/models
v1/completions
v1/chat/completions
v1/embeddings

Scaled
Function 
Deployment 
Solution

72

72

LLM Interfaces
The Whole Stack

api.nvcf.
nvidia.com
/v2/nvcf

health.api.nvidia.com/
ai.api.nvidia.com/

integrate.api.nvidia.com

v1/models
v1/completions
v1/chat/completions
v1/embeddings

api.openai.com

v1/models
v1/completions
v1/chat/completions
v1/embeddings

NVIDIABase

OpenAI

Scaled
Function 
Deployment 
Solution

73

73

LLM Interfaces
The Whole Stack

api.nvcf.
nvidia.com
/v2/nvcf

health.api.nvidia.com/
ai.api.nvidia.com/

integrate.api.nvidia.com

v1/models
v1/completions
v1/chat/completions
v1/embeddings

api.openai.com

v1/models
v1/completions
v1/chat/completions
v1/embeddings

NVIDIABase

OpenAI

Scaled
Function 
Deployment 
Solution

74

74

LLM Interfaces
The Whole Stack

api.nvcf.
nvidia.com
/v2/nvcf

health.api.nvidia.com/
ai.api.nvidia.com/

integrate.api.nvidia.com

v1/models
v1/completions
v1/chat/completions
v1/embeddings

api.openai.com

v1/models
v1/completions
v1/chat/completions
v1/embeddings

ChatNVIDIA

NVIDIABase

ChatOpenAI

OpenAI

Scaled
Function 
Deployment 
Solution

75

75

Building RAG Agents with LLMs
Part 3: Intro to LangChain

76

LangChain Structure

77

Chain Building
Just The LLM

Input

LLM

Output

Hey 
There

LLM

AIMessage(“Hello”
)

79

79

Chain Building
Simple Prompt+LLM Chain

Input

Prompt

LLM

Output

{‘input’ : 
“Hey There”}

Prompt
Context: {context}
Input: {input}

Hey 
There

LLM

AIMessage(“Hello”
)

80

80

Chain Building
Simple Prompt+LLM Chain

Input

Prompt

LLM

Output

chain = prompt | chat
chain.invoke(inputs)

{‘input’ : 
“Hey There”}

Prompt
Context: {context}
Input: {input}

Hey 
There

LLM

AIMessage(“Hello”
)

81

81

Chain Building
Simple Prompt+LLM Chain

Input

Prompt

LLM

Output

## StrOutputParser()
def get_content(value):

return getattr(value, “content”, value)

chain = prompt | chat
chain.invoke(inputs)

| get_content

{‘input’ : 
“Hey There”}

Prompt
Context: {context}
Input: {input}

Hey 
There

LLM

AIMessage(“Hello”
)

82

82

Chain Building
Invoking Runnables

Input

Prompt

LLM

Output

chain = prompt | chat | StrOutputParser()

83

83

Chain Building
Invoking Runnables

Input

Prompt

LLM

Output

chain = prompt | chat | StrOutputParser()

msg = chain.invoke(...)

for token in chain.stream(...)

84

84

Chain Building
Building Information Pipelines

Input

Prompt

LLM

Output

External

85

85

Chain Building
Building Information Pipelines

Input

Prompt

LLM

Output

External

Input

Prompt

LLM

Prompt

LLM

Output

If/Else

Prompt

Internal

Database

Output

86

86

LangChain Extended Ecosystem

https://github.com/langchain-ai/langchain/tree/master

87

87

Our Environment
Jupyter Notebooks + Frontend
+ LLM Client

:8090

Remote Host

Frontend

:9012

Your Device
Docker
Router

LLMs

:9000

:88

Jupyter Notebook Server

88

88

Building RAG Agents with LLMs
Part 4: Running State Chain

89

Chain Building
Recall Our Assumptions

Input

Prompt

LLM

What to do?

External

Prompt

LLM

Output

No Lookup

If/Else

Needs Lookup

Prompt

Internal

Off-Topic

Database

Output

90

90

Chain Building
Towards Running State

Input

Prompt
Classify 
Sentence

LLM

Topic

inputs = {‘input’ : ‘sentence’}
cls_chain = cls_prompt | llm
topic = cls_chain.invoke(inputs)

91

91

Chain Building
Towards Running State

Input

Prompt
Classify 
Sentence

LLM

Topic

Prompt
Generate 
Sentence

LLM Output

inputs = {‘input’ : ‘sentence’}
cls_chain = cls_prompt | llm
topic = cls_chain.invoke(inputs)

gen_chain = out_prompt | llm
out_chain = cls_chain | gen_chain
for token in out_chain.stream(inputs):

print(token, end=””)

92

92

Chain Building
Towards Running State

Input

Prompt
Classify 
Sentence

LLM

Prompt
Generate 
Sentence

LLM

Output

Prompt
Combine 
Sentences

LLM

Output

Input

inputs = {‘input’ : ‘sentence’}
new_sentence = out_chain.invoke(inputs)

93

93

Chain Building
Towards Running State

Input

Prompt
Classify 
Sentence

LLM

Prompt
Generate 
Sentence

LLM

Output

Prompt
Combine 
Sentences

LLM

Output

Input

inputs = {‘input’ : ‘sentence’}
new_sentence = out_chain.invoke(inputs)

inputs.update({‘new’ : ‘new_sentence’})
for token in merge_chain.stream(inputs):

print(token, end=””)

94

94

Chain Building
Towards Running State

Input

Prompt
Classify 
Sentence

LLM

Prompt
Generate 
Sentence

LLM

Output

Branch Chain

Prompt
Combine 
Sentences

LLM

Output

RunnableAssign

Input

Branch Chain

out_chain = RunnableAssign({

new_sentence : cls_chain | gen_chain

}) | merge_chain

95

95

Typical Running State
Regular Fibonacci w/ While Loop

96

96

Running State Chain Components
Towards LCEL While Loop 

State
n = 8
fib = [0,1]

97

97

Running State Chain Components
Towards LCEL While Loop 

State
n = 8
fib = [0,1]

State
n = 7
fib = [0,1,1]
msg=“Hello”

98

98

Running State Chain Components
Towards LCEL While Loop 

State
n = 8
fib = [0,1,1]

[0,1,1,2]

99

99

Running State Chain Components
Towards LCEL While Loop 

State
n = 8
fib = [0,1,1]

[0,1,1,2]

State
n = 8
fib = [0,1,1,2]

100

100

Running State Chain Components
Towards LCEL While Loop 

State
n = 8
fib = [0,1,1]

State
n = 8
fib = [0,1,1,2]

State
n = 8
fib = 
[0,1,1,2, 3]

101

101

Final Running State Loop

102

102

Typical Running State Loop
Comparing Typical with Running State

103

103

Final Running State Loop
Big Picture

RunnableAssign

RunnableLambda

RunnableBranch

104

104

Airline Chatbot

+Knowledge 
Base

+Response

Input

Prompt
Update 
Knowledge

LLM

DB 
Lookup

Prompt
Format

Prompt
Update 
Knowledge

LLM

+Customer 
Info

History

User

105

105

Modern Chain Paradigms
Towards Powerful Running State

Prompt LLM

Unstructured 
Generation

Input

106

106

Modern Chain Paradigms
Towards Powerful Running State

Prompt LLM

Unstructured 
Generation

Prompt

Code
LLM

Environment

Structured 
Retrieval

Input

https://python.langchain.com/docs/use_cases/qa_structured/sql

107

107

Modern Chain Paradigms
Towards Powerful Running State

Prompt LLM

Unstructured 
Generation

Prompt

Code
LLM

Environment

Structured 
Retrieval

Input

Prompt LLM

Grammar
/Schema

Guided 
Generation

{“first_name” : “unknown”,

“last_name”  : “unknown”,
“confirmation” : -1}
Update given new info:
“Sure, my name is Jane Doe!”

{“first_name” : “Jane”,
“last_name”  : “Doe”,
“confirmation” : -1}

LLM

108

108

Modern Chain Paradigms
Towards Powerful Running State

Prompt LLM

Unstructured 
Generation

Prompt

Code
LLM

Environment

Structured 
Retrieval

Input

Prompt LLM

Grammar
/Schema

Guided 
Generation

Prompt LLM

Tool 
Choice

Tool

Tooling

Tool 
Schema

109

109

Final Objective
Knowledge Base + Running State Chain

{

“first_name” : “unknown”,
“last_name”  : “unknown”,
“confirmation” : -1,
...

}
Update given new info:
“Sure, my name is Jane Doe!”

{

}

“first_name” : “Jane”,
“last_name”  : “Doe”,
“confirmation” : -1,
...

LLM

110

110

Airline Chatbot

+Knowledge 
Base

+Response

Input

Prompt
Update 
Knowledge

LLM

DB 
Lookup

Prompt
Format

Prompt
Update 
Knowledge

LLM

+Customer 
Info

111

111

Airline Chatbot

+Knowledge 
Base

+Response

Input

Prompt
Update 
Knowledge

LLM

DB 
Lookup

Prompt
Format

Prompt
Update 
Knowledge

LLM

+Customer 
Info

112

112

Airline Chatbot

+Knowledge 
Base

+Response

Input

Prompt
Update 
Knowledge

LLM

DB 
Lookup

Prompt
Format

Prompt
Update 
Knowledge

LLM

+Customer 
Info

History

User

113

113

Building RAG Agents with LLMs
Part 5: Working with Documents

114

Modern Chain Paradigms
Towards Powerful Running State

Prompt LLM

Unstructured 
Generation

Prompt

Code
LLM

Environment

Structured 
Retrieval

Input

Prompt LLM

Grammar
/Schema

Guided 
Generation

Prompt LLM

Tool 
Choice

Tool

Tooling

Tool 
Schema

115

115

Document Reasoning

Prompt
Context 
Question

LLM

Sure, I can 
answer by 
referring this 
blog post!

https://developer.nvidia.com/blog/

116

116

Document Reasoning

Company
Database

Prompt
Context 
Question

LLM

Sure, I can 
answer by 
referring this 
blog post!

117

117

Company
Database

Local 
files

Your Device

Document Reasoning

Prompt
Context 
Question

LLM

Sure, I can 
answer by 
referring this 
blog post!

118

118

Document Reasoning

Prompt
Context 
Question

LLM

Sure, I can 
answer by 
referring this 
blog post!

Company
Database

Local 
files

Your Device

https://js.langchain.com/docs/use_cases/question_answering/

119

119

Company
Database

Local 
files

Your Device

Document Reasoning

Prompt
Context………
…………………………
…………………………
…………………………
…………………………
…………………………
…………………………
…………………………
…………………………
…………………………
…………………………
…………………………
…………………………
…………………………
…………………………
Question

LLM

I forgot the 
instructions, but 
I can still say 
things

https://js.langchain.com/docs/use_cases/question_answering/

https://d2l.ai/

120

120

Chunking 

https://arxiv.org/pdf/2307.09288.pdf

121

121

Document Stuffing 

Prompt

(DOCS 1-4)

Use Them 
Please

Question

LLM

Oh yes, the intro 
tells me 
everything! You 
see…

https://arxiv.org/pdf/2307.09288.pdf

122

122

Map Reduce Chain

Prompt
Useful Info

LLM

Smaller 
Chunk

Smaller 
Chunk

Smaller 
Chunk

⠇

https://arxiv.org/pdf/2307.09288.pdf

123

123

Refinement Chain

Top 10 
Chunks

for doc in docs:

yield doc

Prompt
Useful Info

LLM

Summary

https://arxiv.org/pdf/2307.09288.pdf

124

124

Main 
Ideas

Knowledge Graph Construction

Prompt
Useful 
Constructs

Prompt
Chapter 
Logic

for doc in docs:

yield doc

Abstraction 
Main Ideas

LLM

Abstractions

LLM

Chapters

Prompt
Character 
Information

LLM

Names

https://blog.langchain.dev/using-a-knowledge-graph-to-implement-a-devops-rag-application/

Per-Chapter 
Main Ideas

Identity Key 
Points

125

125

Knowledge Graph Traversal

Abstraction 
Main Ideas

How does Flying 
work according to 
your book?

Prompt
Find Info

LLM

Abstractions

Prompt
Use Info

LLM

Sure! From the 
chapter on Birds, 
I can tell you…

https://blog.langchain.dev/using-a-knowledge-graph-to-implement-a-devops-rag-application/

Chapters

Names

Per-Chapter 
Main Ideas

Identity Key 
Points

126

126

Refinement Chain
Your Assignment

Top 10 
Chunks

for doc in docs:

yield doc

Prompt
Useful Info

LLM

Summary

https://arxiv.org/pdf/2307.09288.pdf

127

127

Main 
Ideas

Refinement Chain
Your Assignment

RunnableLambda

for doc in docs:

yield doc

Prompt
Useful Info

LLM

Summary

https://arxiv.org/pdf/2307.09288.pdf

128

128

Optional Tangent: LangGraph

https://python.langchain.com/docs/langgraph/
https://blog.langchain.dev/langgraph-multi-agent-workflows/
129

129

Refinement Chain
Your Assignment

RunnableLambda

for doc in docs:

yield doc

Prompt
Useful Info

LLM

Summary

https://arxiv.org/pdf/2307.09288.pdf

130

130

Building RAG Agents with LLMs
Part 6: Embedding Model for Retrieval

131

Knowledge Graph Traversal

Abstraction 
Main Ideas

How does Flying 
work according to 
your book?

Prompt
Find Info

LLM

Abstractions

Prompt
Use Info

LLM

Sure! From the 
chapter on Birds, 
I can tell you…

https://blog.langchain.dev/using-a-knowledge-graph-to-implement-a-devops-rag-application/

Chapters

Names

Per-Chapter 
Main Ideas

Identity Key 
Points

132

132

Modern Chain Paradigms
Towards Powerful Running State

Prompt LLM

Unstructured 
Generation

Prompt

Code
LLM

Environment

Structured 
Retrieval

Input

Prompt LLM

???

Unstructured 
Retrieval

Unstructured 
Retrieval

133

133

Modern Chain Paradigms
Towards Powerful Running State

Prompt LLM

Unstructured 
Generation

Prompt

Code
LLM

Environment

Structured 
Retrieval

Input

Prompt LLM

Vector

Database

Unstructured 
Retrieval

Unstructured 
Retrieval

134

134

Transformer Architecture
Primary Backbone of LLMs

Element-Wise 
Feed-Forward

Sequence 
Attention 
Interface

Element-Wise 
Feed-Forward

Element-Wise 
Feed-Forward

Sequence 
Attention 
Interface

Element-Wise 
Feed-Forward

https://arxiv.org/pdf/1706.03762.pdf

136

136

Transformer Architecture
Autoregressing vs Embedding Flavors

137

137

Transformer Architecture
Autoregressing vs Embedding Flavors

138

138

Retrieval QA Embedding
Asymmetric Query/Document Model

https://catalog.ngc.nvidia.com/orgs/nvidia/teams/ai-foundation/models/nvolve-29k/api

139

Embedding and Comparing
Querying for Semantically Similar Entries

High-performance computing.

Happy Holidays!

DLSS Gaming Statistics

Any cool video games lately?

Biological vision structure

What’s with GPUs these days?

Mitochondria, powerhouse

https://developer.nvidia.com/blog/accelerating-vector-search-using-gpu-powered-indexes-with-rapids-raft/

140

Embedding and Comparing
Querying for Semantically Similar Entries

High-performance computing.

Happy Holidays!

DLSS Gaming Statistics

Any cool video games lately?

Biological vision structure

What’s with GPUs these days?

Mitochondria, powerhouse

https://developer.nvidia.com/blog/accelerating-vector-search-using-gpu-powered-indexes-with-rapids-raft/

141

Embedding and Comparing
Querying for Semantically Similar Entries

High-performance computing.

Happy Holidays!

DLSS Gaming Statistics

Any cool video games lately?

Biological vision structure

What’s with GPUs these days?

Mitochondria, powerhouse

https://developer.nvidia.com/blog/accelerating-vector-search-using-gpu-powered-indexes-with-rapids-raft/

142

Language Embedding Schemes
Bi-Encoder versus Cross-Encoder

Bi-Encoder

Embedding

Cross-Encoder

Reranker

Cosine-Similarity

u

v

Encoder

Encoder

Classifier

Encoder

Passage 1

Passage 2

Passage 1

Passage 2

https://www.sbert.net/examples/applications/cross-encoder/README.html

144

Language Embedding Schemes
Symmetric versus Asymmetric

Symmetric

Asymmetric/Generalized

Cosine-Similarity

u

v

Encoder 1

Encoder 1

Passage 1

Passage 2

https://www.sbert.net/examples/applications/cross-encoder/README.html

https://cs.stanford.edu/~myasu/blog/racm3/

145

Language Embedding Schemes
Generalized Definition

https://cs.stanford.edu/~myasu/blog/racm3/

146

Embedding and Comparing
Querying for Semantically Similar Entries

High-performance computing.

Happy Holidays!

DLSS Gaming Statistics

Any cool video games lately?

Biological vision structure

What’s with GPUs these days?

Mitochondria, powerhouse

https://developer.nvidia.com/blog/accelerating-vector-search-using-gpu-powered-indexes-with-rapids-raft/

147

Building RAG Agents with LLMs
Part 6.4: Guardrails

148

Embedding and Comparing
Querying for Semantically Similar Entries

High-performance computing.

Happy Holidays!

DLSS Gaming Statistics

Any cool video games lately?

Biological vision structure

What’s with GPUs these days?

Mitochondria, powerhouse

https://developer.nvidia.com/blog/accelerating-vector-search-using-gpu-powered-indexes-with-rapids-raft/

149

Semantic Guardrails

Illegal 
Topics

Irrelevant 
Questions

How’s the 
weather?

Classifier
Branch

Prompt
Answer 
Please 
Question

Prompt
Don’t 
Answer 
question

Tell me about 
GPUs

What’s an 

LLM Service What’s a good 
game with RTX?

LLM

No. I shouldn’t 
answer that

150

150

Embedding Classification
Classifying with embeddings

Illegal 
Topics

Irrelevant 
Questions

Tell me about 
GPUs

What’s an 

LLM Service What’s a good 
game with RTX?

https://developer.nvidia.com/blog/accelerating-vector-search-using-
gpu-powered-indexes-with-rapids-raft/

151

Embedding Classification
Classifying with embeddings

Illegal 
Topics

Irrelevant 
Questions

Tell me about 
GPUs

What’s an 
LLM Service

What’s a good 
game with RTX?

https://developer.nvidia.com/blog/accelerating-vector-search-using-
gpu-powered-indexes-with-rapids-raft/

152

Embedding Classification
Classifying with embeddings

Illegal 
Topics

Irrelevant 
Questions

Classification Head

0 or 1?

Tell me about 
GPUs

What’s an 

LLM Service What’s a good 
game with RTX?

https://developer.nvidia.com/blog/accelerating-vector-search-using-
gpu-powered-indexes-with-rapids-raft/

153

Semantic Guardrails

Illegal 
Topics

Irrelevant 
Questions

How’s the 
weather?

Classifier
Branch

Prompt
Answer 
Please 
Question

Prompt
Don’t 
Answer 
question

Tell me about 
GPUs

What’s an 

LLM Service What’s a good 
game with RTX?

LLM

No. I shouldn’t 
answer that

154

154

Building RAG Agents with LLMs
Part 7: Document Retrieval with Vector Databases

155

Embedding and Comparing
Querying for Semantically Similar Entries

High-performance computing.

Happy Holidays!

DLSS Gaming Statistics

Any cool video games lately?

Biological vision structure

What’s with GPUs these days?

Mitochondria, powerhouse

https://developer.nvidia.com/blog/accelerating-vector-search-using-gpu-powered-indexes-with-rapids-raft/

156

Retrieval-Augmented Generation
Pulling in Information from a Database

https://www.nvidia.com/en-us/training/instructor-led-workshops/rapid-application-development-using-large-language-models/

https://cs.stanford.edu/~myasu/blog/racm3/

157

Retrieval QA Embedding
Asymmetric Query/Document Model

https://catalog.ngc.nvidia.com/orgs/nvidia/teams/ai-foundation/models/nvolve-29k/api

158

158

Integrating a Vector Store

159

159

Integrating a Vector Store

https://engineering.fb.com/2017/03/29/data-infrastructure/faiss-a-library-for-efficient-similarity-search/ 160

160

Integrating a Vector Store

VDB

https://engineering.fb.com/2017/03/29/data-infrastructure/faiss-a-library-for-efficient-similarity-search/ 161

161

Integrating a Vector Store

VDB

Retriever

https://engineering.fb.com/2017/03/29/data-infrastructure/faiss-a-library-for-efficient-similarity-search/

162

162

Integrating a Vector Store

VDB

Retriever

<metadata> 
your name is NVBot…

<conversation> 
Hey, my name is Jane
<wikipedia> 
…a name is a term…

https://engineering.fb.com/2017/03/29/data-infrastructure/faiss-a-library-for-efficient-similarity-search/

163

163

Retrieval Reordering/Selection

What’s
my name?

VDB

Retriever

<metadata> 
your name is NVBot…

<conversation> 
Hey, my name is Jane
<wikipedia> 
…a name is a term…

Reranker

LongContextReorder

164

164

Query Augmentation

What’s
my name?

Prompt
Rephrase as 
Question

LLM

Prompt
Rephrase as 
Hypothesis

LLM

VDB

Retriever

165

165

RAG Fusion

What’s
my name?

Prompt
Rephrase as 
Question

LLM

Prompt
Rephrase as 
Hypothesis

LLM

VDB

Retriever

Reranker

166

166

Integrating a Vector Store

https://faiss.ai/

167

167

Integrating a Local Vector Store

Local Host

Milvus Standalone

Frontend

Your Device

Jupyter Notebook

FAISS

https://faiss.ai/

168

168

Integrating a Local Vector Store

Local Host

Milvus 
Standalone

Frontend

Your Device

Jupyter Notebook

FAISS

<s>[INST]<<SYS>>
{{system_message}}
<</SYS>>

{{instruction}} [/INST] 
{{primer}}

Llama

Mistral

Query Router

“context”:{{context}}
“model”:“query”/”doc”

E5

{

}

doc1
doc2
doc3

169

169

GPU-Accelerating Vector Stores

https://developer.nvidia.com/blog/accelerating-vector-search-using-gpu-powered-
indexes-with-rapids-raft/

https://engineering.fb.com/2017/03/29/data-
infrastructure/faiss-a-library-for-efficient-similarity-
search/

170

170

Compute Scale Progression

Milvus Cluster

Milvus Standalone

Jupyter Notebook
Server      .FAISS

https://developer.nvidia.com/blog/making-data-science-teams-productive-kubernetes-rapids/

171

171

Simple Conversation RAG Setup

Hello! My 
name is Jane
Hello Jane! 
How are you?

What’s My Name?

VDB
Retriever

Retriever
VDB

Prompt
History
Context
Question

LLM

It’s Jane!

172

172

Simple RAG Agents

How does RAG 
work?

Classifier
Branch

Prompt
Question

Prompt
Context
Question

LLM

Sure! According 
to the paper…

Retriever

VDB

173

173

Proper RAG Agent
Tool-Selection Agents

TOOLSET

How does RAG 
work?

Prompt
Context
Question

LLM

LLM Data 
Retriever

Prompt
What Should 
I do?

LLM

Final Answer
+ History

Prompt
Question
Answer

LLM

174

174

Building RAG Agents with LLMs
Part 8: RAG Evaluation

175

LLM-As-A-Judge
Pipeline Evaluation

RAG Pipeline

How does 
RAG work?

Prompt
Context
Question

LLM

According to 
my resources…

Retriever

176

176

LLM-As-A-Judge
Pipeline Evaluation

RAG Pipeline

How does 
RAG work?

Prompt
Context
Question

LLM

According to 
my resources…

Retriever

Prompt
Facilitate 
Testing

LLM

Functions

Evaluation Pipeline

Prompt
Is This 
Good?

LLM

Functions

177

177

Our Evaluation Chain Components
Synthetic Generation

VDB

Doc1

Doc2

Prompt
Ask+Answer

LLM

Q: How Does 
RAG Work?
A: From these 
documents…

178

178

Our Evaluation Chain Components
RAG Pipeline Sample

VDB

Doc1

Doc2

Prompt
Ask+Answer

LLM

Q: How Does 
RAG Work?
A: From these 
documents…

How does 
RAG work?

Prompt
Context
Question

LLM

According to 
my resources…

Retriever

179

179

Our Evaluation Chain Components
Ground Truth vs Our Pipeline

VDB

Doc1

Doc2

Prompt
Ask+Answer

LLM

Q: How Does 
RAG Work?
A: From these 
documents…

How does 
RAG work?

Prompt
Context
Question

LLM

According to 
my resources…

Retriever

Prompt
Which Is 
Better?

LLM

[1] Bot 2 Better

180

180

Our Evaluation Chain Components
Ground Truth vs Our Pipeline

VDB

Doc1

Doc2

Prompt
Ask+Answer

LLM

Q: How Does 
RAG Work?
A: From these 
documents…

How does 
RAG work?

Prompt
Context
Question

LLM

According to 
my resources…

Retriever

Prompt
Which Is 
Better?

LLM

[1] Bot 2 Better

[0]

[1]

[0]

[1]

[1]

4/6

181

181

General Evaluation Chain Components
Multiple Metrics at Once

RagasEvaluatorChain

VDB
+ Embedder

LLM

{question}

Prompt
Context
Question

LLM

Retriever

https://github.com/explodinggradients/ragas

182

182

RAG Evaluation with 
Quantifying System Goodness with LLM-as-a-Judge

Control

Sources

Input

RagasEvaluatorChain

https://arxiv.org/pdf/2307.09288.pdf

183

RAG Evaluation with 
Quantifying System Goodness with LLM-as-a-Judge

https://arxiv.org/pdf/2307.09288.pdf

https://github.com/explodinggradients/ragas/blob/main/src/ragas/metrics/_faithfulness.py

184

Evaluator Agent
Pipeline Evaluation

Prompt
Ask some 
questions

LLM

Prompt
What Should 
I do?

LLM

Chain to 
Evaluate

TOOLSET

Final Answer
+ History

Prompt
Is This 
Good?

LLM

185

185

Our Evaluation Chain Components
Ground Truth vs Our Pipeline

VDB

Doc1

Doc2

Prompt
Ask+Answer

LLM

Q: How Does 
RAG Work?
A: From these 
documents…

How does 
RAG work?

Prompt
Context
Question

LLM

According to 
my resources…

Retriever

Prompt
Which Is 
Better?

LLM

[1] Bot 2 Better

[0]

[1]

[0]

[1]

[1]

4/6

186

186

Evaluate RAG In The Frontend
Final Assessment

Remote Host

Frontend

Your Device

Jupyter Notebook

:8090

RAG

NVIDIA 
GPU CLOUD

187

187

Congratulations!
AND THANK YOU SO MUCH!

188