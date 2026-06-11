# Hooks

Hooks allow you to run custom scripts or shell commands at specific points during Antigravity's execution loop. This is powerful for enforcing custom rules, running linters, or capturing diagnostics automatically.

## Configuration

Hooks are configured in a `hooks.json` file located in your customization directory (e.g., `.agents/` in your workspace or `~/.gemini/config/`).

## Schema and File Format

The `hooks.json` file maps hook names to their event configurations.

```json
{
  "my-linter-hook": {
    "PostToolUse": [
      {
        "matcher": "run_command",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/lint.sh",
            "timeout": 10
          }
        ]
      }
    ]
  },
  "safety-gate": {
    "enabled": false,
    "PreToolUse": [
      {
        "matcher": "run_command",
        "hooks": [
          {
            "command": "./scripts/safety-check.sh"
          }
        ]
      }
    ]
  },
  "reminder": {
    "PreInvocation": [
      {
        "type": "command",
        "command": "./scripts/reminder.sh"
      }
    ]
  }
}
```

### Hook Definition Fields

| Field | Type | Description |
| --- | --- | --- |
| `enabled` | boolean | Optional. Set to `false` to disable the hook without removing it. Defaults to `true`. |
| `PreToolUse` | array | Handlers that run before a tool is executed. |
| `PostToolUse` | array | Handlers that run after a tool completes. |
| `PreInvocation` | array | Handlers that run before Antigravity calls the model. |
| `PostInvocation` | array | Handlers that run after tool calls finish. |
| `Stop` | array | Handlers that run when the execution loop terminates. |

## Supported Events

| Event | Description | Matcher Target |
| --- | --- | --- |
| `PreToolUse` | Fires before a tool is executed. | Tool name (e.g., `run_command`) |
| `PostToolUse` | Fires after a tool completes. | Tool name |
| `PreInvocation` | Fires before the model is called. | N/A (matcher ignored) |
| `PostInvocation` | Fires after tool calls finish. | N/A (matcher ignored) |
| `Stop` | Fires when execution terminates. | N/A (matcher ignored) |

### Matcher

For `PreToolUse` and `PostToolUse`, you can use a regular expression in the `matcher` field to specify which tools trigger the hook:

* `""` or `"*"`: Match all tools.
* `"run_command"`: Match exactly `run_command`.
* `"run_command|view_file"`: Match either tool.
* `"browser_.*"`: Match any tool starting with `browser_`.

**Note**: For `PreInvocation`, `PostInvocation`, and `Stop`, the structure is simpler and the matcher is ignored.

## Supported Tools

For `PreToolUse` and `PostToolUse` matchers, you can match against the following tool names:

### File and Directory Operations
* `view_file`, `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `list_dir`, `find_by_name`

### Search and Research
* `grep_search`, `search_web`, `read_url_content`

### System and Execution
* `run_command`, `manage_task`, `schedule`, `list_permissions`, `ask_permission`

### Agent Collaboration
* `invoke_subagent`, `define_subagent`, `send_message`, `manage_subagents`

### Interaction and Media
* `ask_question`, `generate_image`

## Hook Handler Configuration

| Field | Type | Description |
| --- | --- | --- |
| `type` | string | Optional. Currently only `"command"` is supported. Defaults to `"command"`. |
| `command` | string | Required. The shell command to execute. |
| `timeout` | integer | Optional. Timeout in seconds. Defaults to `30`. |

## Input/Output Contract

Hooks receive input via **stdin** as JSON and should return output via **stdout** as JSON.

### Common Input Fields

All hooks receive the following system metadata fields in their input payload on `stdin`:

| Field | Type | Description |
| --- | --- | --- |
| `conversationId` | string | The unique UUID of the active agent conversation. |
| `workspacePaths` | array of strings | Absolute directory paths representing the user's mounted workspaces. |
| `transcriptPath` | string | The absolute path to the persistent `transcript.jsonl` conversation logs. |
| `artifactDirectoryPath` | string | The absolute path to the directory containing all conversation artifacts and screenshots. |

---

### PreToolUse

Fires before a tool is executed.

**Output Fields (stdout)**:
* `decision`: **Required.** Controls how the tool call is gated: `"allow"`, `"deny"`, `"ask"`, or `"force_ask"`.
* `reason`: **Optional.** The explanation shown to the agent or user for the decision.
* `permissionOverrides`: **Optional.** A list of resource strings to override default tool permissions.

---

### PostToolUse

Fires after a tool completes.

**Input Fields (stdin)**:
* `stepIdx`: The 0-based index of the completed step.
* `error`: Optional. The detailed runtime error message if the tool call failed.

---

### PreInvocation

Fires before the model is called.

**Output Fields (stdout)**:
* `injectSteps`: **Optional.** List of steps to inject into the conversation trajectory before the model is called.

---

### PostInvocation

Fires after tool calls finish.

**Output Fields (stdout)**:
* `injectSteps`: **Optional.** List of steps to inject after the invocation completes.
* `terminationBehavior`: **Optional.** Controls the execution flow after injection (`"force_continue"`, `"terminate"`, or omitted).

---

### Stop

Fires when the execution loop terminates.

**Output Fields (stdout)**:
* `decision`: **Required.** Set to `"continue"` to prevent the agent from stopping and re-enter the execution loop.
* `reason`: **Optional.** If `decision` is `"continue"`, this message is injected as a system message.
