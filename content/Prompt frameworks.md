# Prompt frameworks

Prompt Frameworks for Improving
Chatbot Responses

A Guide to Effective LLM Interaction



Introduction to Prompt Engineering

 What is Prompt
Engineering?

The art and science of designing
effective instructions for AI models

Crafting targeted queries

Structuring input for optimal

output

Guiding LLM behavior and
responses

 Why is it Important?

Bridge between human intent and

AI capability

Maximizes model performance

Reduces errors and
hallucinations

Ensures consistent, reliable

outputs

 Impact on LLM
Responses

Well-engineered prompts can
improve response quality by up to

57%

Enhanced accuracy and

relevance

Better structured and formatted

outputs

More consistent results across
queries

Popular AI Chatbots Overview

Comparison of leading AI chatbots and their key capabilities

Chatbot

LLM

Key Features

 ChatGPT

GPT-4o / GPT-4o mini

 Copilot

GPT-4 Turbo

 Claude

Claude 3 family

 Perplexity AI

GPT-4 Turbo, Claude 3

 Jasper

Multiple LLMs

 You.com

Custom LLM

•

•

•

•

•

•

•

•

•

•

•

•

•

•

•

•

•

•

Text generation, math, coding

Advanced conversation capabilities

Web browsing, data analysis, file uploads

Internet access & current events

Image/document uploads

Voice feature, image generation

Pricing

Free

Free

Privacy-focused (no training on user data)

Free / Pro $20/mo

Document uploads

Coding, math, writing, research

Internet-connected with sources

Free / Pro $20/mo

Footnotes with references

Photos & graphics in answers

Marketing copy generation

Grammar & plagiarism checking

50+ templates, SEO insights

Search engine functionality

Real-time web results

Conversational responses

$49+/mo

Free / Pro $15/mo

Understanding Prompt Frameworks

 What are Prompt Frameworks?

 Why Use Them?

Structured templates for crafting effective prompts

Frameworks improve response quality and consistency

Provide consistent structure

Clarify intent and requirements

Guide LLM thinking process

 Five Key Frameworks

Reduce ambiguity and confusion

Increase task completion accuracy

Save time through structured approach

R-T-F

T-A-G

Role-Task-Format

Task-Action-Goal

R-I-S-E

Role-Input-Steps-
Example

R-G-C

Role-Goal-
Constraints

C-A-R-E

Content-Action-
Result-Example

R-T-F Framework (Role-Task-Format)

 Framework Overview

Structured approach for straightforward requests

Define the Role the LLM should adopt

Specify the Task or action required

Indicate the desired Format for output

Best for: Simple tasks like converting transcripts to meeting

minutes, summarizing content, or generating standard
documents

Role

↓

Task

↓

Format

 ChatGPT Example

 Prompt

 Response

Role: You are an executive assistant.

Meeting Minutes - [Date]

Task: Take the attached zoom transcript and convert it into

meeting minutes. Add as many topics and bullet points as
necessary.

Format: Include date, attendees, agenda items, key decisions,
and action items with owners and deadlines.

Attendees: [List of attendees]

Agenda Items:
[Topic 1 with key points]

[Topic 2 with key points]
Key Decisions:

[Decision 1]
[Decision 2]

Action Items:
[Action] - [Owner] - [Deadline]

T-A-G Framework (Task-Action-Goal)

 Framework Overview

Goal-oriented approach for focused responses

Describe the Task at hand

State the Action you want the LLM to take

Articulate the specific Goal to maintain focus

Best for: Analysis tasks, problem-solving, and when you need

specific outcomes with measurable results

 Copilot Example

 Prompt

Task: Summarize key insights from a product analytics report.

Action: Highlight the top 3 usage trends.

Goal: Identify potential new feature ideas that could increase
customer engagement by 20%.

Task

↓

Action

↓

Goal

 Response

Top 3 Usage Trends:
Mobile usage increased by 35% with peak activity during

evening hours
Feature adoption rates highest among new users within first 7

days
Integration usage up 45% among power users

Potential New Feature Ideas:

Mobile Dashboard: Enhanced analytics view for mobile users
Onboarding Wizard: Guided feature tour for new users

Advanced API: Expanded integration capabilities for power
users

R-I-S-E Framework (Role-Input-Steps-Example)

 Framework Overview

Comprehensive approach for complex tasks

Specify the Role for the LLM to adopt

Provide key Inputs to inform response

Ask for exact Steps required

Give relevant Example for context

Best for: Complex problem-solving, creative tasks, and when

the LLM needs to ask clarifying questions

Role

↓

Input

↓

Steps

↓

Example

 Claude Example

 Prompt

 Response

Role: Act as a UX researcher at a software startup.

Recommended Additional Metrics:

Input: User interviews indicate our dashboard lacks key
analytics.

Steps: Suggest additional metrics and data visualizations.

Example: Google Analytics dashboard.

User engagement time per feature
Conversion funnel visualization

User retention by cohort
Feature adoption rate over time

Data Visualization Suggestions:

Interactive heatmaps for user activity
Trend lines with comparative periods

Customizable dashboard widgets
Real-time data streaming for key metrics

Would you like me to elaborate on any of these suggestions or

discuss implementation considerations?

R-G-C Framework (Role-Goal-Constraints)

 Framework Overview

Constraint-based approach for focused outputs

Provide the Role for the LLM

Define the desired Goal or outcome

Give specific Constraints to work within

Best for: Custom GPTs, content creation with specific

guidelines, and when outputs need to follow strict

parameters

Role

↓

Goal

↓

Constraints

 Perplexity AI Example

 Prompt

 Response

Role: You specialize in creating social media posts for blog
content, targeting platforms like Twitter, LinkedIn, and Reddit.

Twitter Post:
Discover how AI is transforming customer service! Our latest

Goal: Summarize key points from the blog posts and craft posts
that are engaging, professional, and tailored to each platform's

audience.

Constraints: Posts should maintain a balance between

professionalism and inspiration, and formatted for each
platform's character limits and style.

blog reveals 5 key strategies businesses are implementing to
improve response times by 60%. #AI #CustomerService

#Innovation

LinkedIn Post:
Customer service is undergoing a revolution with AI integration.

Our comprehensive analysis shows businesses implementing AI-
powered solutions are seeing significant improvements in

customer satisfaction and operational efficiency. Learn about
the top 5 strategies leading this transformation.

Reddit Post:

r/technology: Just published an in-depth look at how AI is
reshaping customer service. We analyzed data from 100+

companies and found some surprising results about response
time improvements and customer satisfaction. Curious to hear

your thoughts on these findings!

 Sources: Social Media Examiner, HubSpot, Sprout Social

C-A-R-E Framework (Content-Action-Result-Example)

 Framework Overview

Example-driven approach for consistent outputs

Set context with background Content

State the Action you want the LLM to take

Articulate the desired Result

Provide a relevant Example to guide the model

Best for: Content creation, brand voice consistency, and

when you need outputs that match specific styles or formats

Content

↓

Action

↓

Result

↓

Example

 You.com Example

 Prompt

 Response

Content: We are rebuilding our company's customer loyalty

Tech-Focused Loyalty Benefits:

program.

Action: Recommend potential new benefits and perks.

Result: Ideas customized for tech-savvy users that incentivize
engagement.

Example: Amazon Prime's model of free shipping and media
streaming.

Early Access: Priority access to new product releases and beta
features

Digital Library: Unlimited access to premium tech content,
courses, and tutorials

Tech Support: 24/7 premium technical support with reduced
wait times

Cloud Storage: Expanded storage capacity for all your digital
assets

Engagement Incentives:

Tech Community: Exclusive access to forums and expert Q&A
sessions

Rewards Multiplier: Bonus points for tech reviews and
community contributions

Partner Perks: Discounts on leading tech brands and software
subscriptions

Best Practices and Tips

 Effective Techniques

 Common Mistakes

 Advanced Strategies

Be specific and clear in your
instructions

Vague instructions leading to
inconsistent results

Use chain-of-thought for complex
reasoning

Provide context and background
information

Overloading prompts with too
many requirements

Apply few-shot learning for
specialized tasks

Use examples to illustrate desired
output

Assuming knowledge the LLM
doesn't have

Implement prompt chaining for
multi-step processes

Break complex tasks into smaller
steps

Not providing examples for
complex outputs

Set clear boundaries and
constraints

Iterate and refine prompts based
on results

Ignoring formatting needs for the
response

Test prompts across different
models

 Further Learning Resources

 Prompt Engineering Guide  OpenAI Documentation  AI Communities  Research Papers