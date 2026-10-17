package com.nutrifit.model;
public record ChatMessage(long id, long conversationId, String senderRole, String content) {}
