package com.nutrifit.dto;
import com.nutrifit.model.FeatureCode;
public record FeatureAccessDTO(FeatureCode code,String module,String displayLabel,String requiredTier,boolean unlocked) {}
