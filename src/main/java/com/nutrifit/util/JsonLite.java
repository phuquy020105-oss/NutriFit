package com.nutrifit.util;

import java.util.*;

/** Small standalone JSON encoder/parser for Gemini HTTP. Replace with Jackson when approved in pom.xml. */
public final class JsonLite {
    private JsonLite() {}
    public static String quote(String s){
        StringBuilder b=new StringBuilder("\"");
        for(char ch:s.toCharArray()){
            switch(ch){
                case '"' -> b.append("\\\"");
                case '\\' -> b.append("\\\\");
                case '\b' -> b.append("\\b");
                case '\f' -> b.append("\\f");
                case '\n' -> b.append("\\n");
                case '\r' -> b.append("\\r");
                case '\t' -> b.append("\\t");
                default -> {if(ch<32)b.append(String.format("\\u%04x",(int)ch));else b.append(ch);}
            }
        }
        return b.append('"').toString();
    }
    public static Object parse(String json){
        Parser p=new Parser(json);Object o=p.value();p.ws();
        if(p.i!=json.length())throw new IllegalArgumentException("Invalid JSON trailing data");return o;
    }
    private static final class Parser {
        final String s;int i;Parser(String s){this.s=s;}
        void ws(){while(i<s.length()&&Character.isWhitespace(s.charAt(i)))i++;}
        char peek(){ws();if(i>=s.length())throw new IllegalArgumentException("Unexpected end");return s.charAt(i);}
        char take(){return s.charAt(i++);}
        void expect(char c){if(peek()!=c)throw new IllegalArgumentException("Expected "+c);i++;}
        Object value(){char c=peek();return switch(c){
            case '"' -> str();case '{' -> obj();case '[' -> arr();
            case 't' -> lit("true",Boolean.TRUE);case 'f' -> lit("false",Boolean.FALSE);
            case 'n' -> lit("null",null);default -> num();};}
        Object lit(String v,Object result){if(!s.startsWith(v,i))throw new IllegalArgumentException("Invalid literal");i+=v.length();return result;}
        Object obj(){expect('{');Map<String,Object> m=new LinkedHashMap<>();if(peek()=='}'){i++;return m;}
            do{String k=str();expect(':');m.put(k,value());if(peek()=='}'){i++;return m;}expect(',');}while(true);}
        Object arr(){expect('[');List<Object> a=new ArrayList<>();if(peek()==']'){i++;return a;}
            do{a.add(value());if(peek()==']'){i++;return a;}expect(',');}while(true);}
        String str(){expect('"');StringBuilder b=new StringBuilder();while(i<s.length()){
            char c=take();if(c=='"')return b.toString();if(c!='\\'){b.append(c);continue;}
            if(i>=s.length())break;char e=take();switch(e){
                case '"','\\','/' -> b.append(e);case 'b' -> b.append('\b');case 'f' -> b.append('\f');
                case 'n' -> b.append('\n');case 'r' -> b.append('\r');case 't' -> b.append('\t');
                case 'u' -> {if(i+4>s.length())throw new IllegalArgumentException("Bad unicode");
                    b.append((char)Integer.parseInt(s.substring(i,i+4),16));i+=4;}
                default -> throw new IllegalArgumentException("Invalid escape");
            }
        }throw new IllegalArgumentException("Unterminated string");}
        Object num(){int begin=i;while(i<s.length()&&"-+0123456789.eE".indexOf(s.charAt(i))>=0)i++;
            if(begin==i)throw new IllegalArgumentException("Invalid number");return Double.parseDouble(s.substring(begin,i));}
    }
}
