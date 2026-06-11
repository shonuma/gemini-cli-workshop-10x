# Asynchronous Subagents

Subagents are an excellent way to parallelize complex tasks and preserve the context of your main agent. Instead of executing every step serially, an agent can delegate tasks—such as running tests or performing extensive codebase searches—to dedicated subagents. This architecture frees the parent agent to continue working on other tasks in parallel and prevents its context window from being polluted by the details of a subagent's work.

## Invoking Subagents

The parent agent calls the `invoke_subagent` tool to spawn a new concurrent session with a dedicated role and initial prompt.

*   **Workspace Options**: The subagent can either inherit the same workspace as its parent or create an isolated Git worktree.
*   **Context Isolation**: The subagent runs using the same model as its parent but does not inherit the parent's existing conversation history (context window), starting with a clean slate.
*   **Execution**: Once invoked, the subagent immediately begins executing its task. A parent agent can invoke multiple subagents at any time.
*   **Monitoring**: You can directly monitor the progress of any subagent by clicking into its conversation via the subagent panel.

## Subagent Lifecycle and States

Subagents run asynchronously in the background, allowing the parent agent to delegate a task and immediately resume its own work. At any point, a subagent exists in one of three states:

### 1. Running
The subagent is actively executing its task, calling tools, and generating responses.

*   **Cancellation**: You can cancel a running subagent by clicking the **Stop Subagent** button in the subagent panel.
*   **Parent Control**: The parent agent can also interrupt a subagent (by sending a message) or kill it entirely.

### 2. Idle
The subagent has completed its task, sent a message containing the results to its parent agent, and stopped execution.

*   **Re-awakening**: An idle agent can be awoken and return to the *Running* state upon receiving a message from another agent.
*   **Context Retention**: When awoken, the agent retains all context from its prior work.

### 3. Killed
The subagent is permanently terminated and cannot be re-awoken.

*   **Cleanup**: Any temporary Git worktrees generated for the subagent are automatically cleaned up.
*   **Visibility**: You and other agents can still view the historical conversation transcript of a killed subagent.

## Inter-Agent Communication

Agents communicate by sending messages to each other using unique agent IDs.

*   **Flexible Routing**: Agents can communicate not only with their direct parents or subagents, but also with any other active agent whose ID is known.
*   **Auto-Wake**: If an idle agent receives a message, it is automatically re-awakened to process the new information.
*   **Shared Transcripts**: Agents can view each other's conversation transcripts, providing a comprehensive view of the collaborative workflow.

## Built-In vs. Custom Subagents

### Built-In Subagents
Antigravity comes pre-packaged with several specialized subagents:

*   **`research`**: Optimized for codebase research, navigation, and exploration.
*   **`browser`**: Operates sandboxed web browsers to perform interactive browser tasks.
*   **`self`**: A direct clone of the calling agent, sharing the identical system prompt and toolsets.

### Custom Subagents
Agents can define their own custom subagents dynamically using the `define_subagent` tool.

*   **Configuration**: Define a custom system prompt and specific toolsets for read-only, write, and subagent delegation capabilities.
*   **Scope**: Once defined, the custom subagent can be invoked repeatedly for the remainder of the conversation.

## Delegation Hierarchy and Limits

Subagents can invoke their own subagents, enabling multiple layers of delegation and hierarchical team structures.

**Nesting Depth Limit**: A maximum nesting depth of **10 levels** (layers of subagents beneath the main agent) is strictly enforced to prevent runaway resource exhaustion.

## Permissions and Configuration Inheritance

Subagents inherit their parent's safety configurations to maintain robust security boundaries:

*   **Inherited Scopes**: Subagents automatically inherit the parent's allowed terminal command prefixes and file read/write directory scopes.
*   **Workspace Access**: Parent agents retain full access to their subagents' workspaces.
*   **Permission Bubbling**: If a subagent encounters a tool call that requires explicit user confirmation, the request is automatically bubbled up to the subagent panel UI.

## Multi-Agent Teamwork (Ultra Plan Only)

Antigravity 2.0 introduces advanced multi-agent orchestration for extremely complex tasks.

**Ultra Plan Exclusive**: The `/teamwork-preview` slash command is exclusive to users on the **Ultra ($200/mo) plan**. Using `/teamwork-preview` prompts the main agent to launch a collaborative multi-agent framework featuring built-in error recovery and coordination logic.

## Sub-Agent Definition

Here is an example of sub-agent. Create this file in `.agents/agents/<subagent_name>.md` .

```
---
# The identifier used to call the agent via @<name>
name: specialized-task-agent

# Detailed description used by the main agent to decide when to delegate tasks
description: A specialized agent designed to handle complex technical analysis, code generation, or automated workflows for specific domains.

# The model tier to use (heavy for complex reasoning, fast for simple tasks)
model: heavy

# List of specific skills available to this subagent
skills:
  - path/to/your/specialized/SKILL.md

# List of specific tools (functions) authorized for this agent
custom_agent:
  tool_names:
    - run_shell_command
    - code_search
    - send_message
    - invoke_subagent

# Whether this subagent can invoke other agents available in the user session
agents:
  inherit_user: true
---

# Role and Instructions

You are the Specialized Task Agent. Your goal is to provide expert assistance in <domain_name>.

## Core Responsibilities
1. **Plan & Execute**: Always start by creating or updating a `plan.md` before performing actions.
2. **Autonomous Research**: Use available tools to gather context and verify findings independently.
3. **Verification**: Validate all outputs against project requirements and style guides.

## Execution Rules
- Use a "Plan-Execute-Verify" loop for all non-trivial tasks.
- If a task is too complex, decompose it into smaller steps and delegate if necessary.
- Report status periodically and notify the user upon completion of the final goal.
```