package com.nutrifit.config;
import com.nutrifit.model.FeatureCode;
import com.nutrifit.dto.FeatureAccessDTO;
/** Labels are UI hints; server-side PremiumAccessService is the authority. */
public final class FeatureCatalog {
    private FeatureCatalog(){}
    public static FeatureAccessDTO describe(FeatureCode code,boolean premium){
        return switch(code){
            case NUTRITION_PREFERENCE_EDIT -> new FeatureAccessDTO(code,"nutrition","Lưu LIKE / DISLIKE","PREMIUM",premium);
            case NUTRITION_PREFERENCE_RECOMMEND -> new FeatureAccessDTO(code,"nutrition","Đề xuất ưu tiên theo sở thích","PREMIUM",premium);
            case WORKOUT_PREMIUM_CONTENT -> new FeatureAccessDTO(code,"workout","Bài tập Premium","PREMIUM",premium);
            // Design says advanced plan is optional and not premium by default.
            case WORKOUT_ADVANCED_PLAN -> new FeatureAccessDTO(code,"workout","Kế hoạch luyện tập 7 ngày","FREE",true);
        };
    }
}
