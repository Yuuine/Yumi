"""
Character Card Model - 角色卡模型
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class CharacterCardBase(SQLModel):
    """角色卡基础模型"""
    user_id: str = Field(index=True)
    conversation_id: Optional[str] = Field(default=None, index=True)
    role_overview: str = Field(default="")
    formal_name: str = Field(default="")
    nickname: str = Field(default="")
    race_or_form: str = Field(default="人类")
    gender: str = Field(default="中性")
    visual_age: str = Field(default="")
    actual_age: str = Field(default="")
    location: str = Field(default="")
    appearance_desc: str = Field(default="")
    core_personality: str = Field(default="")
    self_perception: str = Field(default="")
    attitude_to_user: str = Field(default="")
    likes: str = Field(default="")
    dislikes: str = Field(default="")
    tone_base: str = Field(default="")
    word_habits: str = Field(default="")
    emotion_rules: str = Field(default="")
    length_pref: str = Field(default="")
    special_logic_list: str = Field(default="")
    few_shot_examples: str = Field(default="")
    is_active: bool = Field(default=True)


class CharacterCard(CharacterCardBase, table=True):
    """角色卡表模型"""
    __tablename__ = "character_cards"

    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})


class CharacterCardCreate(CharacterCardBase):
    """创建角色卡模型"""
    id: str


class CharacterCardUpdate(SQLModel):
    """更新角色卡模型"""
    conversation_id: Optional[str] = None
    role_overview: Optional[str] = None
    formal_name: Optional[str] = None
    nickname: Optional[str] = None
    race_or_form: Optional[str] = None
    gender: Optional[str] = None
    visual_age: Optional[str] = None
    actual_age: Optional[str] = None
    location: Optional[str] = None
    appearance_desc: Optional[str] = None
    core_personality: Optional[str] = None
    self_perception: Optional[str] = None
    attitude_to_user: Optional[str] = None
    likes: Optional[str] = None
    dislikes: Optional[str] = None
    tone_base: Optional[str] = None
    word_habits: Optional[str] = None
    emotion_rules: Optional[str] = None
    length_pref: Optional[str] = None
    special_logic_list: Optional[str] = None
    few_shot_examples: Optional[str] = None
    is_active: Optional[bool] = None
