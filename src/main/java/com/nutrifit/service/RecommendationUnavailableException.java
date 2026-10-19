package com.nutrifit.service;

/** Only fixed, safe user-facing explanations belong in this exception. */
public class RecommendationUnavailableException extends IllegalArgumentException {
    public RecommendationUnavailableException(String message) { super(message); }
}
