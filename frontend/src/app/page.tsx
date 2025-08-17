"use client"

import React from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { ArrowRight, Sparkles, Rocket, PenLine, ImageIcon } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-primary/5 via-background to-background">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none [mask-image:radial-gradient(75%_60%_at_50%_0%,#000_20%,transparent_60%)]">
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-[1200px] h-[1200px] rounded-full bg-primary/10 blur-3xl" />
        </div>

        <div className="max-w-6xl mx-auto px-6 pt-20 pb-12 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border bg-card/70 backdrop-blur text-sm mb-6">
            <span className="text-muted-foreground">Ribbit: Articles in minutes</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-foreground leading-tight">
            Create rank-ready articles in minutes with
            <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent"> Ribbit</span>
          </h1>

          <p className="mt-4 text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto">
            Research, write, and optimize across industries and languages with the click of a button.
          </p>

          {/* Search/Input Bar */}
          <div className="mt-8 mx-auto max-w-3xl">
            <div className="flex items-center gap-2 p-2 rounded-2xl border shadow-lg bg-card/70 backdrop-blur">
              <Input placeholder="Describe your agent..." className="h-12 text-base flex-1" />
              <Link href="/blog">
                <Button className="h-12 px-6 btn-primary">
                  Write with AI <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>

            <div className="mt-4 flex flex-wrap justify-center gap-2 text-sm text-muted-foreground">
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full border">Product Description</span>
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full border">Instagram Caption</span>
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full border">Write a blog post</span>
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full border">Email Sequence</span>
            </div>
          </div>

          {/* Trust Logos */}
          <div className="mt-10">
            <p className="text-sm text-muted-foreground mb-4">Trusted by more than 1,000+ teams</p>
            <div className="grid grid-cols-2 md:grid-cols-6 gap-6 items-center opacity-80">
              {['Census','HEX','Spot.ai','SwapQ','Replcart','Unity'].map((logo) => (
                <div key={logo} className="h-10 rounded-md border flex items-center justify-center text-sm text-muted-foreground">
                  {logo}
                </div>
              ))}
            </div>
            <div className="mt-4 flex justify-center">
              <Link href="/dashboard">
                <Button variant="outline" size="sm">See more studios</Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center">How our AI writer works</h2>
          <p className="text-muted-foreground text-center mt-2 max-w-2xl mx-auto">
            Input information about your business or product, and let our agents research, plan, and generate SEO-ready articles.
          </p>

          <div className="mt-8 grid md:grid-cols-3 gap-6">
            <Card className="card-hover">
              <CardContent className="p-6">
                <Sparkles className="h-8 w-8 text-primary" />
                <h3 className="font-semibold mt-4">Plan</h3>
                <p className="text-sm text-muted-foreground mt-2">Our planning agent researches your topic and prepares an outline.</p>
              </CardContent>
            </Card>
            <Card className="card-hover">
              <CardContent className="p-6">
                <PenLine className="h-8 w-8 text-primary" />
                <h3 className="font-semibold mt-4">Write</h3>
                <p className="text-sm text-muted-foreground mt-2">Generate long-form drafts in your tone and brand style.</p>
              </CardContent>
            </Card>
            <Card className="card-hover">
              <CardContent className="p-6">
                <Rocket className="h-8 w-8 text-primary" />
                <h3 className="font-semibold mt-4">Publish</h3>
                <p className="text-sm text-muted-foreground mt-2">Export to your CMS and social channels with one click.</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Feature Preview cards */}
      <section className="pb-24">
        <div className="max-w-6xl mx-auto px-6 grid md:grid-cols-3 gap-6">
          <Card className="card-hover">
            <CardContent className="p-0">
              <div className="aspect-video bg-muted/40 flex items-center justify-center">
                <ImageIcon className="h-10 w-10 text-muted-foreground" />
              </div>
              <div className="p-6">
                <h3 className="font-semibold">Blog generator</h3>
                <p className="text-sm text-muted-foreground mt-1">Create SEO-ready blog posts.</p>
                <Link href="/blog">
                  <Button className="mt-4">Open <ArrowRight className="ml-2 h-4 w-4" /></Button>
                </Link>
              </div>
            </CardContent>
          </Card>
          <Card className="card-hover">
            <CardContent className="p-0">
              <div className="aspect-video bg-muted/40 flex items-center justify-center">
                <ImageIcon className="h-10 w-10 text-muted-foreground" />
              </div>
              <div className="p-6">
                <h3 className="font-semibold">Social media</h3>
                <p className="text-sm text-muted-foreground mt-1">Generate platform-optimized posts.</p>
                <Link href="/social">
                  <Button className="mt-4" variant="outline">Open <ArrowRight className="ml-2 h-4 w-4" /></Button>
                </Link>
              </div>
            </CardContent>
          </Card>
          <Card className="card-hover">
            <CardContent className="p-0">
              <div className="aspect-video bg-muted/40 flex items-center justify-center">
                <ImageIcon className="h-10 w-10 text-muted-foreground" />
              </div>
              <div className="p-6">
                <h3 className="font-semibold">Analytics</h3>
                <p className="text-sm text-muted-foreground mt-1">Monitor performance and system health.</p>
                <Link href="/monitoring">
                  <Button className="mt-4" variant="ghost">Open <ArrowRight className="ml-2 h-4 w-4" /></Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  )
}
