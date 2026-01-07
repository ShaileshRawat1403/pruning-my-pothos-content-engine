# Agentic

Introduction to LLMs and Agentic AI 
with Applications in Service Sciences

with Applications in Service Sciences

Tomáš Brázdil

Neural Networks

Real vs artificial

Neural Network

How does it work?

Neuron

Neuron

Neuron

Neuron

because

What is it good for? Dog recognition! (and other animals)

Supervised learning: Training on large amounts of data of the following form: 

[        , Dog], [        , Cat], [     , chair] …

Some History: ILSVRC 2012

Image recognition competition

●
●

1 200 000 images
1 000 classes (dog, chair, …)

Top 5 evaluation = correct class among the first five by the model

AlexNet - Winner of 2012

Error rate 15.3 percent!

The second runner 26.2 percent!

ILSVRC

2016: Error under three percent … data no longer useful …

Big problem:

Where to get 
large useful data?

● Manual annotation no longer possible.
● How to train models without explicit 

feedback?

● How to model reasoning?

Reinforcement learning

A. Geron, Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow 3rd Edition, 2022

How computers play tic-tac-toe?

Random play:

Human (o) Machine (x)

Learning:
● Computer plays for all both players, starts with 0 weight on all choices
● After win/loss increment/decrement values of choices made in the play

Implementation in 1961? MENACE!

● Single box for each configuration of pieces
● Shake the box, one ball falls out, play accordingly
● Used balls and boxes stored along the play
● Learning:

○ At the beginning, each box has the same number 

of balls (relevant for the move)

○ Repeatedly play from the beginning to the end

■ If win, for every used box and ball, put the ball 

and 3 more of the same color to the box
■ If los, do not return balls to the used boxes

Atari 2600

2013: AI plays Atari 2600

NN sees the Atari 2600 display
Uses joystick

Learns just from wins/loses in 
the game

Q-learning

Mnih et al., Human-level control through deep reinforcement learning, Nature, 2015

How well it plays?

Superhuman performance in most 
games

Some games very bad

Later much improved … nowadays 
AI plays all Atari 2600 games well

Breakout

Language Models

How is all this related to language models?

Text generation can be seen as a machine learning problem:

Show examples of generation to a model, then let it generate.

The usual approach:

● Self-supervised learning - fill in the next word in a partial sentence
● Supervised fine-tuning - learn from specific human examples of text 

continuation

● Reinforcement learning with human feedback - improve model by letting it 

play with words

But first we need the appropriate model.

Language processing

● How to encode words into vectors? Embeddings

● How to process sentences? 

Sentences have different lengths, neural networks have fixed input dim.

dog -> [0.1, 0.2, -11, …, 1.6]
cat -> [0.2, 0.1, -10, …, 1]

● How to encode language understanding?

The dog jumped over the cat.
The dog ate the cat’s meal and then left.

Why would a dog jump over a cat?

One-Hot Word Embedding

Vocabulary V

|V| = size of V

One-Hot embedding
● High dim
● Sparse
● Not suitable for 
neural networks

Word Embedding of Dimension 10 (Word2Vec)

2D t-SNE Projection of Embedding Vectors (Word2Vec)

Semantically similar 
words should be 
close to each other

Word Embeddings

Many embedding methods exist, most of them based on the following idea:

“a word is characterized by the company it keeps” John R. Firth (1957)

That is, the semantics of a word is implied by its context.

Methods are

● Classical (non-neural): TF-IDF, LSA, LDA, …
● Neural models: Word2Vec, GloVe, …

Let’s not get bogged down by details …

Processing Sentences

Crucial problem: Sentences have variable length.

“Standard” neural network:

Fixed number of inputs

Recurent neural network (Rosenblatt 1960)

[0.5,...,-1.2]

[-0.1,...,23]

[...,]

[...,]

=>

[0,...,0]

The red stuff = internal 
representation of the 
sentence prefix read so far 
(the state vector)

      Hi

   are 

 are      you

Reads sequence/sentence sequentially … quickly forgets what it has seen, 
Sentence “squashed” into the state vector, does not preserve context well

Attention is what you need!

[0.5,...,-1.2]

[-0.1,...,23]

[...,]

[...,]

=>

[0,...,0]

      Hi

   are 

 are      you

The red stuff = internal 
representation of the 
sentence prefix read 
so far

Green arrows = the 
attention connections 
for ht

Reads sequence/sentence sequentially but also looks at the relevant 
context when generating the output words

Attention is ALL you need!

[0.5,...,-1.2]

[-0.1,...,23]

[...,]

[...,]

[0,...,0]

      Hi

   are 

 are      you

Knows context when generating each ht 
More efficient, parallelizable

The red stuff = internal 
representation of the 
sentence prefix read 
so far

Green arrows = the 
attention connections 
for ht

Attention is ALL you need

Drop the recurrent network and leave just the attention -> works better!

Result: GPT model, beginning of LLM era!

Taken from https://newsletter.theaiedge.io/p/understanding-the-self-attention

Taken from https://newsletter.theaiedge.io/p/understanding-the-self-attention

Taken from https://newsletter.theaiedge.io/p/understanding-the-self-attention

Application: Bias detection

GPT-3

● Reads an incomplete text - a sequence of words (embeddings)

x1, x2, …, xk

● Transforms it several times using the self-attention (and other types of 

layers) into final embeddings

e1, e2, …, ek

● Transforms the final embeddings into probabilities of the next words:

P( x2 | x1), P( x3 |x1,x2),..., P( xk+1 | x1,...,xk)

● Predicts the next word in the sentence using P( xk+1 | x1,...,xk)
● A high probability word is selected as the next one in the sentence

LARGE Language Models

LLM Training

Three phases:

Self-supervised

Supervised

Reinforcement learning

Self-Supervised LLM

Self-supervised learning … guess the next word

Trained on extremely 
large corpuses of data

Huge data and 
computing resources
(thousands of GPUs)

GPT-3 Training

… yes, obsolete but illustrates the scale:

● 175 billion trained parameters (weights)
● Trained on 45TB of data

LLM - Supervised-training

The point: Training data may contain sequences of question without answers.

LLM - Supervised training

… don’t say rubbish just because others do 

LLM - Reinforcement Learning

Examples of mistakes:

Necessary to be
● helpful
● honest
● harmless

Apparently learning 
from a mass of 
human texts is not 
satisfactory

Reinforcement Learning from Human Feedback (RLHF)

Base model = trained LLM - determines a strategy choosing answers (actions)

Preference model = evaluates answers (actions) chosen by LLM
… trained using human preferences individual LLM answers

LLM World
… opens for you

How to Use LLMs - OpenAI Illustration

Models

● GPT-3
● GPT-4

8,192 tokens input

● DALL-E

text to image generation

● GP-4o, etc.

Completion API

Simple, generates 
continuations of the prompts.

Completion API - some parameters

● max_tokens - max number of tokens in the generated text 

-> important, you pay for tokens!

● temperature - controls the randomness of the output of the model

● Top_p - pick only top p probable words

Parameters Temperature and top_p

Completion API - some parameters

Logit_bias (-100, 100) - likelihood of specified tokens appearing in the completion 

GPT-3.5-turbo logic gate:

Chat completion API

Facilitate interactive conversations - chatbot implementation

Three roles:

● System

used to set chatbot behavior, 
provides model with high-level instructions guiding behavior,
included in every API call.

● User

user’s input in conversation

● Assistant 

the chatbot answer

user and assistant take turns in conversation

Example

Output

Finish_reason values:

stop
length
content_filter
Tools_call
function_call
null

Prompting
… machine learning level 2

Prompting - few shot learning

Self-consistency Sampling

Try several times (possibly using different models), take the “best” answer:
● E.g. majority voting
● Agentic: Use another LLM agent to decide, what is best

Self-consistency Sampling

Lost in the middle

Empirical result: The performance is 
best if the information is present at the 
context window’s beginning or end.

The position of the passage that 
answers the question changing

Becoming Agentic

Function calls

Allow models to use external tools at their will
Implemented via calls to python functions

If the model decides to call the function, it returns response with response.output:

Now you may call the function (and do whatever you want)

Example

The chatbot may record questions it cannot answer

The function may, e.g., 
store the question into 
database for further 
examination

This mechanism can 
be used to implement 
RAG

Retrieval-Augmented Generation (RAG)

Combine external data with LLM knowledge

Advantages of using RAG

● Up-to-date knowledge (assuming that it’s present in the resources)

LLM has been trained on data up to some time instant
Direct update of LLM is expensive (need to retrain the large model)

● Fact-checking and “grounding”

LLM may give direct references to resources (that may of course be also false but you may 
check)
Grounding - connecting model’s outputs to actual external data

● Local information resources

Companies utilize their large databases of materials, e.g., how-to-do chatbots

● Scalable

You may keep adding resources if you have technology for their operation

RAG gives agents their long-term memory

Simple implementation of RAG with vector databases

● Text knowledge database

● Chunks of text dataset stored:

Simple implementation of RAG

Chunks indexed by vector 
embeddings

Allows similarity search

retrieve : embed query, find chunks with similar embeddings, return top_n similar

Put the relevant chunks into the intruction_prompt for the chatbot

Finally, call the model:

Now all this can be iterated, various resources used, memory updated, etc.

There are various memory types, vector indexed, SQL databases, etc.

Chunking is an art in itself: Short or long chunks? Depends on the text, context, etc.

Example: Code Generation

Already many LLM based tools exist

Cursor

● LLM based (primarily Claude but supports others)
● Autocompletion & chat based
● LLM integrated with the editor
● Features

○ Can understand your codebase
○ Runs terminal commands
○ Error detector
○ References the codebase (shows relevant places in your code that may solve the problem)
○ …

See yourself https://www.cursor.com/features

Fun with web page code (Cursor)

My initial prompt: I want you to create web portal, locally hosted, which has a standard 
layout of marketing web pages and contains a "HIT ME" button which makes a tex "Have 
been hit" appear on the page in red color!

The LLM generated HTML, CSS and JavaScript code underlying a server and the 
web-page (a slight overkill for a web page but fair enough)

The code had two easily corrected typos in CSS

The LLM instructed me to open the html page

My next prompt: give me a script that allows me to execute this on linux self hosted

Created a sh script start_server.sh, applied chmod +x start_server.sh and told 
me to run the script 
(that I managed, who knows what it would have done if I would not be able to execute the script)

Fun with web page code (cont.)

My next prompt: 

now add my email address 
xbrazdil@gmail.com to 
the contacts with my 
name Tomas Brazdil

More complex situation

Programming OAuth library using Claude model, expert comments:

“Initially, I was fairly impressed by the code.“ - all code in one file but well structure, not too many 
comments … generated tests do not have sufficient coverage but at least some were generated

“A more serious bug is that the code that generates token IDs is not sound: it generates biased 
output. This is a classic bug when people naively try to generate random strings”

In other words, LLM may repeat “standard” errors made by humans

“The engineers clearly had a good idea of many aspects of the design, and the LLM was tightly 
controlled and produced decent code. (LLMs are absolutely good at coding in this manner). But it 
still tried to do some stupid stuff, some of which were caught by the engineers, some were not. I’m 
sure some are still in there. Is this worse than if a human had done it? Probably not” 

https://neilmadden.blog/2025/06/06/a-look-at-cloudflares-ai-coded-oauth-library/

AI Agents

Some History

● History of agentic AI reaches back to Turing’s work on machine intelligence 

and Wiener’s work on feedback systems.

● Agents equipped with

○ Perception
○ Planning
○ Reasoning
○
○ Acting

Learning

Have been present in AI development for decades
(See e.g. Artificial Intelligence: A Modern Approach by Russell and Norvig, first edition published in 1995)

● All reinforcement learning, game playing and autonomous systems literature 

has naturally been agentic

What is all the fuss about Agents now?

Power the agents with LLM brains.

Human vs LLM Agent Workflow

Tools

Using tools:

Planning

Agent prompted to decompose into steps:
● Prompt with “Let’s think step by step”
● Or better be more precise and ask for 

a plan for carrying out the plan

Planning

The agent can be 
instructed to use 
specific tools in 
steps, etc.

Short-term : Prompt context, 
RAG

Long-term : RAG

May store (embeddings of) 
interactions and search

May store generated 
summaries, where the agent 
decides, what to remember
(combined with reflection)

Memory

Note the red 
feedback arrow:

By modifying 
memory the agent 
implements 
long-term 
memory

Memory types

● Working memory: The Immediate Context
Implementation: Store the past messages

● Episodic memory: Learning from the past

Implemented using RAG, two ways

○ Store past conversations and then search
○ Feedback-driven: Receive feedback on 

the performance (possibly by another agent) 
-> update the memory

Memory types

● Semantic memory: Store knowledge
Key-value pairs, knowledge graphs

Memory types

● Procedural memory: How-to

Functions or agents represent the skills

Workflow

1. Take a user’s message
2. Create a system prompt with relevant Episodic enrichment
3.
4. Create a Semantic memory message with context from the database
5. Reconstruct the entire working memory to update the system prompt and 

Insert procedural memory into prompt

attach the semantic memory and new user messages to the end

6. Generate a response with the LLM

Example

Generated prompt: "Based on my previous experience assisting Dr. Smith with a colonoscopy AI analysis 
on June 3rd (episodic memory), and using the standardized diagnostic criteria for ulcerative colitis from the 
ECCO guidelines (semantic memory), I will now pre-process the new biopsy slides using the same 
segmentation workflow (procedural memory). Currently, I’m holding the patient metadata and the slide IDs 
in temporary storage (working memory), so I can match them with the existing histological models. Let’s 
initiate inference and flag any slides with a Nancy Index score above 3."

● Working Memory: Holds current patient metadata and slide IDs temporarily for 

immediate use during task execution.

● Episodic Memory: Recalls a specific past experience, assisting Dr. Smith on June 3rd, 

to inform current judgment or preference.

● Procedural Memory: Applies a learned process (e.g., image pre-processing and 

segmentation workflow) to perform a task.

● Semantic Memory: Uses abstracted knowledge or general facts. Here, the ECCO 

guidelines and Nancy Index definition for ulcerative colitis severity.

OpenAI SDK

Some Definitions

● Handoffs: The new agent takes over the conversation, and gets to see the 

entire previous conversation history.

● Tool call: Agent calls a function.
● Guardrails:

○

Input guardrails:

■ Receive user input for the model
■

If the input satisfies tripwire conditions, raises exception

○ Output guardrails:

■ Receive output of the model
■

If the output satisfies tripwire conditions, raises exception

Illustration: Agent definition

Illustration: Agent definition

Guardrails

Model Context Protocol (USB-C of AI)

MCP = protocol for 
connecting (remote) 
tools with AI apps

Host (AI app) contains 
MCP client(s)

MCP clients connect 
with MCP servers that 
provide tools in a 
unified form

Allows seamless INTEGRATION of tools!

OpenAI SDK - MCP

The two servers expose file system and web browsing tools to the LLM

Manufacturing Maintenance

CMAPSS dataset - 
Aero-Propulsion System Simulation

Prognostics and Health Management (PHM) 
models for predictive maintenance

source of industrial data to demonstrate 
the system’s ability to interact with a dynamic environment

Manufacturing Maintenance

root_agent : decomposes user intent into
Expectations, Conditions, Targets, Context and 
Information
Plans and delegates to other agents

data_agent : retrieves engine telemetry, predicts 
RUL (in this simulation they predicted from dataset)

maintenance_agent : plans maintenance using 
tools:

– suggest_maintenance_action
– estimate_maintenance_cost
– assign_maintenance_staff
– schedule_maintenance_task

root_agent receives outputs of the data_agent 
and autonomously decides whether to invoke 
maintenance_agent for preventive action 
or to shut down the engine

 
 
 
 
”I need to maintain all engines working well according to their predicted RUL, avoiding 
unexpected stops, please make a consolidated predictive maintenance plan in a table format.”

Manufacturing Maintenance - Final Plan

According to the human oversight, the actions are correct

Agentic AI

AI Agents vs Agentic AI

A single-task AI Agent. 

vs

A multi-agent, 
collaborative 
Agentic AI system

Agentic AI is a new area where people (sometimes) marvel about agent’s capabilities

Agentic manufacturing optimization

Quoting from Bornet et al. Agentic Artificial Intelligence: Harnessing AI Agents to Reinvent Business, Work 
and Life. Irreplaceable Publishing, 2025

1. Initial Task: The AI agent monitors factory machinery to predict potential breakdowns and minimize downtime. For 
example, it analyzes data from sensors tracking vibration, temperature, and wear.

2. Action Generation: Based on the retrieved insights, the AI generates actionable recommendations:

“The vibration pattern suggests bearing wear in Machine X. Schedule a bearing replacement within the next 72 hours to 
prevent failure.”

3. Automated Feedback Through Revenue Metrics:

●

●

The system tracks the financial outcomes of its actions using predefined indicators, such as reduced downtime, 
lower repair costs, or increased output.
If the maintenance intervention prevents a breakdown, it records this as a positive outcome and links it to the specific 
recommendation and retrieved data.

Agentic manufacturing optimization

Still quoting from Bornet et al. Agentic Artificial Intelligence: Harnessing AI Agents to Reinvent Business, 
Work and Life. Irreplaceable Publishing, 2025

4. Positive Reinforcement Learning:

●
●

The AI reinforces the association between vibration patterns and bearing wear in its predictive model.
It flags the retrieved data as highly relevant for similar issues, improving its retrieval accuracy for future anomalies.

5. Updating the memory:

● Maintenance logs and outcomes from this event are added to the database, creating new knowledge the system can 

draw from in the future.
The system also incorporates cost-benefit analysis, associating specific actions with the revenue saved or generated.

●

6. Adaptive Behavior: Over time, the AI becomes better at identifying subtle signs of failure earlier, optimizing its 
recommendations to reduce costly downtime. It may also learn to prioritize actions based on financial impact, ensuring the most 
critical interventions are addressed first.

Conclusions

We went rapidly through the whole evolution from predictive to agentic AI

● Predictive models trained in supervised manner
● Agents trained using reinforcement learning
● LLM trained using self-supervised, supervised, and reinforcement learning
● LLM Agents training on themselves using prompting and RAG
● Agentic AI training emergent behaviors from collaboration of agents

Keep in mind that the current results are mostly experimental

The main problems: Deployment and monetization!