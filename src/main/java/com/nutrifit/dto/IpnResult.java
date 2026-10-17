package com.nutrifit.dto;
public record IpnResult(String code, String message) {
    public static final IpnResult OK = new IpnResult("00", "Confirm Success");
    public static final IpnResult BAD_HASH = new IpnResult("97", "Invalid Checksum");
    public static final IpnResult UNKNOWN = new IpnResult("01", "Order not Found");
    public static final IpnResult INVALID_AMOUNT = new IpnResult("04", "Invalid Amount");
    public static final IpnResult ALREADY_PROCESSED = new IpnResult("02", "Order already confirmed");
    public static final IpnResult ERROR = new IpnResult("99", "Unknown error");
}
