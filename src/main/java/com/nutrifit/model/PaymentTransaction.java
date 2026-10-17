package com.nutrifit.model;
public record PaymentTransaction(long id, long userId, long planId, long amountVnd, String txnRef, String status) {}
