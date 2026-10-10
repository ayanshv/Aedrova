"""Ephemeral UI fixtures. No networking, authentication or durable chat storage."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Message:
    id: str
    author: str
    initials: str
    time: str
    body: str
    tone: int = 0
    decision: bool = False
    attachment: str = ""
    replies: list["Message"] = field(default_factory=list)
    attachment_id: str = ""
    sequence: int = 0
    delivery: str = ""
    mine: bool = False
    unsent: bool = False
    reactions: list[dict] = field(default_factory=list)
    edited: bool = False
    saved: bool = False
    pinned: bool = False
    sender_id: str = ""


@dataclass
class Channel:
    id: str
    name: str
    topic: str
    messages: list[Message] = field(default_factory=list)
    direct: bool = False
    private: bool = False
    description: str = ""
    posting: str = "members"


@dataclass
class Workspace:
    id: str
    name: str
    initials: str
    channels: list[Channel]


class DemoStore:
    """State is deliberately per-window and in-memory until the service milestones."""

    def __init__(self):
        self.workspaces = sample_workspaces()
        self.drafts: dict[tuple[str, str, str], str] = {}

    def workspace(self, workspace_id: str) -> Workspace:
        return next(w for w in self.workspaces if w.id == workspace_id)

    def channel(self, workspace_id: str, channel_id: str) -> Channel:
        return next(c for c in self.workspace(workspace_id).channels if c.id == channel_id)

    def add_workspace(self, name: str) -> Workspace:
        name = name.strip()
        if not 1 <= len(name) <= 32:
            raise ValueError("Use a workspace name between 1 and 32 characters.")
        if any(w.name.casefold() == name.casefold() for w in self.workspaces):
            raise ValueError("A workspace with that name already exists in this preview.")
        initials = "".join(word[0] for word in name.split())[:2].upper()
        workspace = Workspace(
            uuid4().hex,
            name,
            initials,
            [Channel(uuid4().hex, "general", "The beginning of something good.")],
        )
        self.workspaces.append(workspace)
        return workspace

    def add_channel(self, workspace_id: str, name: str, topic: str = "") -> Channel:
        name = "-".join(name.strip().lower().split()).removeprefix("#")
        if not name or len(name) > 32 or not all(c.isalnum() or c in "-_" for c in name):
            raise ValueError("Use 1–32 letters, numbers, hyphens or underscores.")
        workspace = self.workspace(workspace_id)
        if any(c.name == name and not c.direct for c in workspace.channels):
            raise ValueError("That channel already exists.")
        channel = Channel(uuid4().hex, name, topic.strip()[:120] or "A space for your team.")
        workspace.channels.append(channel)
        return channel

    def send(self, workspace_id: str, channel_id: str, body: str, parent_id: str = ""):
        body = body.strip()
        if not body:
            raise ValueError("Write a message first.")
        if len(body) > 10_000:
            raise ValueError("Keep messages under 10,000 characters in this preview.")
        channel = self.channel(workspace_id, channel_id)
        message = Message(
            uuid4().hex, "You", "AV", datetime.now().strftime("%H:%M"), body, 3, mine=True
        )
        if parent_id:
            parent = next(m for m in channel.messages if m.id == parent_id)
            parent.replies.append(message)
        else:
            channel.messages.append(message)
        return message


def sample_workspaces():
    conversation = [
        Message(
            "p1",
            "Alex Morgan",
            "AM",
            "09:41",
            "I've been looking at where people drop off. We ask for too much before they "
            "get to the good part.\nWhat if we made onboarding just three steps?",
            0,
            replies=[
                Message(
                    "r1",
                    "Maya Chen",
                    "MC",
                    "09:43",
                    "Yes. Let's get them into their workspace first.",
                    1,
                )
            ],
        ),
        Message(
            "p2",
            "Maya Chen",
            "MC",
            "09:44",
            "Agreed. Here's a simpler direction: create your workspace, invite your team, "
            "then connect a project. Everything else can wait.",
            1,
            attachment="Onboarding direction.fig · Sample reference",
        ),
        Message(
            "p3",
            "Sam Rivera",
            "SR",
            "09:46",
            "That works with the current auth flow. We can keep Google sign-in and "
            "let people skip invitations until they're ready.",
            2,
        ),
        Message(
            "p4",
            "Alex Morgan",
            "AM",
            "09:48",
            "Let's go with that. Three steps, optional invites, and a clear path into "
            "the workspace. Keep the first screen focused on one thing at a time.",
            0,
            decision=True,
            replies=[
                Message(
                    "r2",
                    "Maya Chen",
                    "MC",
                    "09:49",
                    "I'll keep the layout quiet. One primary action per screen.",
                    1,
                ),
                Message(
                    "r3",
                    "Sam Rivera",
                    "SR",
                    "09:50",
                    "Sounds good. We should preserve the existing sign-in tests.",
                    2,
                ),
            ],
        ),
        Message(
            "p5",
            "Maya Chen",
            "MC",
            "09:52",
            "Perfect. The direction is here whenever we're ready to build.",
            1,
        ),
    ]
    return [
        Workspace(
            "northstar",
            "Northstar Labs",
            "N",
            [
                Channel(
                    "general",
                    "general",
                    "A home for the whole team.",
                    [
                        Message(
                            "g1",
                            "Alex Morgan",
                            "AM",
                            "09:12",
                            "Morning, team. Let's use #product to work through the new onboarding.",
                        )
                    ],
                ),
                Channel(
                    "product", "product", "Ideas, decisions, and what comes next.", conversation
                ),
                Channel(
                    "design",
                    "design",
                    "Make the useful feel effortless.",
                    [
                        Message(
                            "d1",
                            "Maya Chen",
                            "MC",
                            "08:55",
                            "The new direction is simpler: more breathing room, less chrome, "
                            "and one clear action at every step.",
                            1,
                            attachment="Design principles.md · Sample document",
                        )
                    ],
                ),
                Channel(
                    "engineering",
                    "engineering",
                    "Small changes. Thoughtful systems.",
                    [
                        Message(
                            "e1",
                            "Sam Rivera",
                            "SR",
                            "09:20",
                            "For onboarding, let's keep the existing authentication boundary.\n"
                            "Acceptance checks:\n• Google sign-in still works\n"
                            "• Invitations can be skipped\n• Existing sessions stay valid",
                            2,
                        )
                    ],
                ),
                Channel("ideas", "ideas", "Good things often start with a question."),
                Channel(
                    "maya",
                    "Maya Chen",
                    "Direct conversation · local sample",
                    [
                        Message(
                            "dm1",
                            "Maya Chen",
                            "MC",
                            "Yesterday",
                            "I left the onboarding direction in #product. Curious what you think.",
                            1,
                        )
                    ],
                    direct=True,
                ),
                Channel("sam", "Sam Rivera", "Direct conversation · local sample", direct=True),
            ],
        ),
        Workspace(
            "orbit",
            "Orbit Studio",
            "O",
            [
                Channel(
                    "orbit-general",
                    "general",
                    "A place to shape your next idea.",
                    [
                        Message(
                            "o1",
                            "Taylor Brooks",
                            "TB",
                            "10:02",
                            "Welcome to Orbit. This second workspace has its own conversations.",
                            2,
                        )
                    ],
                ),
                Channel("orbit-design", "design", "From a sketch to something real."),
            ],
        ),
    ]
