# -*- coding: utf-8 -*-
# لوحة التحكم: بناء Vite في مرحلة، ثم خدمة الملفات الثابتة وتمرير الـAPI عبر Nginx.

# ---------- مرحلة البناء ----------
FROM node:22-alpine AS build
WORKDIR /app

# طبقة اعتماديات منفصلة كي لا يُعاد npm ci عند تغيير الشيفرة فقط
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---------- مرحلة التشغيل ----------
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --spider http://127.0.0.1/ || exit 1
