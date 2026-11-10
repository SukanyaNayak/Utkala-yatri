// frontend/src/components/PageHero.tsx  (consistent-hero)
//
// ONE hero component for EVERY inner page (Explore, Chat, Planner, Festivals,
// Hotels, Emergency, Gems, Landmark). Same photo, same box, same style on all
// pages — because every page renders THIS component, and the photo comes from
// the single HERO_IMAGE line below instead of per-page props.
//
// HOW TO USE
// 1) Edit ONLY the HERO_IMAGE line below to change the photo on all pages at
//    once. Put your hero.jpg in frontend/public/ (then "/hero.jpg" works), or
//    paste any full https:// image URL.
// 2) In every page, render it WITHOUT an image prop:
//      <PageHero title={t("...")} tagline={t("...")} desc={t("...")} quote={t("...")} />
//    A leftover per-page image="..." still compiles, but delete it — per-page
//    images are exactly what made the pages look different before.
// 3) Home has its own landing hero; if you want the same photo there too,
//      import { HERO_IMAGE } from "../components/PageHero";
//
// Same API as before (title / tagline / desc / quote / image / children), so
// existing calls keep compiling.
"use client";

import type { ReactNode } from "react";

// ⬇️ THE one line to edit — this exact photo appears on EVERY page banner
export const HERO_IMAGE = "/hero.jpg"; // file in frontend/public/ — or an https:// URL

// Shown only if /hero.jpg is missing (e.g. not copied into public/ yet)
const FALLBACK_IMAGE = "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/68a07d073bf8.jpg";

export default function PageHero({
  title,
  tagline,
  desc,
  quote,
  image = HERO_IMAGE,
  children,
}: {
  title: string;
  tagline?: string;
  desc?: string;
  quote?: string;
  image?: string; // deprecated per-page override — remove image="..." from page calls
  children?: ReactNode;
}) {
  return (
    <section className="relative -mx-4 -mt-6 flex min-h-[16rem] flex-col justify-center overflow-hidden rounded-3xl sm:min-h-[20rem]">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={image}
        alt=""
        className="absolute inset-0 h-full w-full object-cover"
        onError={(e) => {
          const el = e.currentTarget;
          if (el.src !== FALLBACK_IMAGE) el.src = FALLBACK_IMAGE;
        }}
      />
      <div className="absolute inset-0 bg-black/30" />

      <div className={`relative px-6 pt-10 text-white sm:px-10 ${children ? "pb-16" : "pb-10"}`}>
        <h1 className="font-script text-5xl sm:text-6xl">{title}</h1>
        {tagline ? (
          <p className="mt-1 text-xs font-semibold tracking-[0.35em] text-white sm:text-sm">{tagline}</p>
        ) : null}
        {desc ? <p className="mt-3 max-w-md text-sm text-white/85">{desc}</p> : null}
        {children ? <div className="mt-6">{children}</div> : null}
      </div>

      {quote ? (
        <p className="absolute right-8 top-6 hidden max-w-[11rem] text-right font-script text-3xl leading-tight text-white md:block">
          {quote}
        </p>
      ) : null}

      {/* torn paper bottom edge blending into the cream page background */}
      <svg viewBox="0 0 1440 60" preserveAspectRatio="none" className="absolute bottom-0 left-0 h-8 w-full">
        <path
          fill="#FFF7EF"
          d="M0,32 C120,44 240,18 360,30 C480,42 600,14 720,26 C840,38 960,12 1080,26 C1200,38 1320,16 1440,30 L1440,60 L0,60 Z"
        />
      </svg>
    </section>
  );
}
