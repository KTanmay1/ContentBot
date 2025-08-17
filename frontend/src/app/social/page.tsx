"use client"

import React, { useState } from 'react'
import { useAppStore } from '@/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  MessageSquare,
  Wand2,
  Clock,
  CheckCircle,
  Image as ImageIcon,
  Copy,
  Download,
  Hash,
  AtSign,
  Sparkles,
  Twitter,
  Facebook,
  Instagram,
  Linkedin
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api'

interface SocialFormData {
  message: string
  platform: string
  contentType: string
  tone: string
  includeHashtags: boolean
  includeImage: boolean
  targetAudience: string
  llmModel: string
}

const platformLimits = {
  twitter: 280,
  facebook: 2200,
  instagram: 2200,
  linkedin: 3000
}

const platformIcons = {
  twitter: Twitter,
  facebook: Facebook,
  instagram: Instagram,
  linkedin: Linkedin
}

export default function SocialMediaGenerator() {
  const { createWorkflow, activeWorkflow } = useAppStore()
  const [formData, setFormData] = useState<SocialFormData>({
    message: '',
    platform: 'twitter',
    contentType: 'promotional',
    tone: 'engaging',
    includeHashtags: true,
    includeImage: false,
    targetAudience: 'general',
    llmModel: 'gemini'
  })
  const [generatedContent, setGeneratedContent] = useState<any>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const handleInputChange = (field: keyof SocialFormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleGenerate = async () => {
    if (!formData.message.trim()) {
      alert('Please enter a message or topic for your social media post')
      return
    }

    setIsGenerating(true)
    setGeneratedContent(null)

    try {
      const inputData = {
        text: formData.message,
        message: formData.message,
        platform: formData.platform,
        content_type: formData.contentType,
        tone: formData.tone,
        include_hashtags: formData.includeHashtags,
        include_image: formData.includeImage,
        target_audience: formData.targetAudience,
        llm_model: formData.llmModel
      }

      const workflowId = await createWorkflow('social_media_generation', inputData)
      
      // Poll for workflow completion
      const pollInterval = setInterval(async () => {
        try {
          const status = await apiClient.getWorkflowStatus(workflowId)
          
          if (status.status === 'completed') {
            clearInterval(pollInterval)
            const result = await apiClient.getWorkflowResult(workflowId)
            
            const characterLimit = platformLimits[formData.platform as keyof typeof platformLimits]
            
            // Ensure we never pass objects to React children
            const tc = result?.text_content
            let content: string = 'Content generation completed.'
            if (typeof tc === 'string') {
              content = tc
            } else if (tc && typeof tc.generated === 'string') {
              content = tc.generated
            }
            
            // Extract hashtags if present inside platform_content or fallback
            const hashtags = Array.isArray(result.platform_content?.hashtags)
              ? result.platform_content.hashtags
              : (formData.includeHashtags ? ['#AI'] : [])
            
            // Transform backend result to frontend format
            setGeneratedContent({
              content,
              hashtags,
              characterCount: content.length,
              characterLimit,
              platform: formData.platform,
              engagement_score: result.quality_scores?.engagement_score || 0,
              readability_score: result.quality_scores?.readability_score || 0,
              image: result.image_content?.generated ? {
                url: result.image_content.generated,
                alt: `${formData.message} visual`,
                description: `Engaging visual for ${formData.platform} post about ${formData.message}`
              } : (formData.includeImage ? {
                url: '/api/placeholder/400/400',
                alt: `${formData.message} visual`,
                description: `Engaging visual for ${formData.platform} post about ${formData.message}`
              } : null)
            })
            setIsGenerating(false)
          } else if (status.status === 'failed') {
            clearInterval(pollInterval)
            throw new Error(status.error || 'Workflow failed')
          }
        } catch (pollError) {
          clearInterval(pollInterval)
          throw pollError
        }
      }, 2000) // Poll every 2 seconds
      
      // Timeout after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval)
        if (isGenerating) {
          setIsGenerating(false)
          alert('Content generation timed out. Please try again.')
        }
      }, 300000)
      
    } catch (error) {
      console.error('Failed to generate social media post:', error)
      setIsGenerating(false)
      alert('Failed to generate content. Please try again.')
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // You could add a toast notification here
  }

  const getCharacterCountColor = (count: number, limit: number) => {
    const percentage = (count / limit) * 100
    if (percentage > 90) return 'text-red-500'
    if (percentage > 75) return 'text-yellow-500'
    return 'text-green-500'
  }

  const PlatformIcon = platformIcons[formData.platform as keyof typeof platformIcons] || MessageSquare

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center space-x-2">
            <MessageSquare className="w-8 h-8 text-primary" />
            <span>Social Media Generator</span>
          </h1>
          <p className="text-muted-foreground mt-1">
            Create engaging social media content for various platforms
          </p>
        </div>
        {activeWorkflow && activeWorkflow.type === 'social_media_generation' && (
          <div className="flex items-center space-x-2 px-3 py-1 bg-muted rounded-lg">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium">Generating...</span>
            <Progress value={activeWorkflow.progress} className="w-20 h-2" />
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Form */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Wand2 className="w-5 h-5" />
                <span>Post Configuration</span>
              </CardTitle>
              <CardDescription>
                Configure your social media post parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Platform */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Platform *</label>
                <Select value={formData.platform} onValueChange={(value) => handleInputChange('platform', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="twitter">
                      <div className="flex items-center space-x-2">
                        <Twitter className="w-4 h-4" />
                        <span>Twitter</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="facebook">
                      <div className="flex items-center space-x-2">
                        <Facebook className="w-4 h-4" />
                        <span>Facebook</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="instagram">
                      <div className="flex items-center space-x-2">
                        <Instagram className="w-4 h-4" />
                        <span>Instagram</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="linkedin">
                      <div className="flex items-center space-x-2">
                        <Linkedin className="w-4 h-4" />
                        <span>LinkedIn</span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Message */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Message/Topic *</label>
                <Textarea
                  placeholder="Enter your message or topic..."
                  value={formData.message}
                  onChange={(e) => handleInputChange('message', e.target.value)}
                  className="min-h-[100px]"
                />
              </div>

              {/* Content Type */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Content Type</label>
                <Select value={formData.contentType} onValueChange={(value) => handleInputChange('contentType', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="promotional">Promotional</SelectItem>
                    <SelectItem value="educational">Educational</SelectItem>
                    <SelectItem value="entertaining">Entertaining</SelectItem>
                    <SelectItem value="inspirational">Inspirational</SelectItem>
                    <SelectItem value="news">News/Update</SelectItem>
                    <SelectItem value="question">Question/Poll</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Tone */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Tone</label>
                <Select value={formData.tone} onValueChange={(value) => handleInputChange('tone', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="engaging">Engaging</SelectItem>
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="casual">Casual</SelectItem>
                    <SelectItem value="humorous">Humorous</SelectItem>
                    <SelectItem value="authoritative">Authoritative</SelectItem>
                    <SelectItem value="friendly">Friendly</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Target Audience */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Target Audience</label>
                <Select value={formData.targetAudience} onValueChange={(value) => handleInputChange('targetAudience', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General Audience</SelectItem>
                    <SelectItem value="professionals">Professionals</SelectItem>
                    <SelectItem value="students">Students</SelectItem>
                    <SelectItem value="entrepreneurs">Entrepreneurs</SelectItem>
                    <SelectItem value="tech_enthusiasts">Tech Enthusiasts</SelectItem>
                    <SelectItem value="creatives">Creatives</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* LLM Model */}
              <div className="space-y-2">
                <label className="text-sm font-medium">LLM Model</label>
                <Select value={formData.llmModel} onValueChange={(value) => handleInputChange('llmModel', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gemini">Gemini</SelectItem>
                    <SelectItem value="mistral">Mistral</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Options */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Include Hashtags</label>
                  <input
                    type="checkbox"
                    checked={formData.includeHashtags}
                    onChange={(e) => handleInputChange('includeHashtags', e.target.checked)}
                    className="rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Include Image</label>
                  <input
                    type="checkbox"
                    checked={formData.includeImage}
                    onChange={(e) => handleInputChange('includeImage', e.target.checked)}
                    className="rounded"
                  />
                </div>
              </div>

              {/* Character Limit Info */}
              <div className="p-3 bg-muted rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Character Limit</span>
                  <Badge variant="outline">
                    {platformLimits[formData.platform as keyof typeof platformLimits]} chars
                  </Badge>
                </div>
              </div>

              {/* Generate Button */}
              <Button
                onClick={handleGenerate}
                disabled={isGenerating || !formData.message.trim()}
                className="w-full"
                size="lg"
              >
                {isGenerating ? (
                  <>
                    <Clock className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generate Post
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Generated Content */}
        <div className="lg:col-span-2 space-y-6">
          {generatedContent ? (
            <>
              {/* Content Header */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center space-x-2">
                      <CheckCircle className="w-5 h-5 text-green-500" />
                      <PlatformIcon className="w-5 h-5" />
                      <span>Generated {formData.platform} Post</span>
                    </CardTitle>
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(generatedContent.content + (generatedContent.hashtags.length > 0 ? '\n\n' + generatedContent.hashtags.join(' ') : ''))}
                      >
                        <Copy className="w-4 h-4 mr-2" />
                        Copy
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className={cn("text-2xl font-bold", getCharacterCountColor(generatedContent.characterCount, generatedContent.characterLimit))}>
                        {generatedContent.characterCount}
                      </div>
                      <div className="text-sm text-muted-foreground">Characters</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">{generatedContent.characterLimit}</div>
                      <div className="text-sm text-muted-foreground">Limit</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">{generatedContent.engagement_score}</div>
                      <div className="text-sm text-muted-foreground">Engagement</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">{generatedContent.readability_score}</div>
                      <div className="text-sm text-muted-foreground">Readability</div>
                    </div>
                  </div>
                  
                  {/* Character Usage Progress */}
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Character Usage</span>
                      <span>{Math.round((generatedContent.characterCount / generatedContent.characterLimit) * 100)}%</span>
                    </div>
                    <Progress 
                      value={(generatedContent.characterCount / generatedContent.characterLimit) * 100} 
                      className="h-2"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Content Preview */}
              <Card>
                <CardHeader>
                  <CardTitle>Content Preview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Main Content */}
                    <div className="p-4 border rounded-lg bg-muted/50">
                      <p className="text-foreground whitespace-pre-wrap">
                        {generatedContent.content}
                      </p>
                    </div>
                    
                    {/* Hashtags */}
                    {generatedContent.hashtags.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium mb-2 flex items-center space-x-1">
                          <Hash className="w-4 h-4" />
                          <span>Hashtags:</span>
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {generatedContent.hashtags.map((hashtag: string, index: number) => (
                            <Badge key={index} variant="secondary" className="cursor-pointer" onClick={() => copyToClipboard(hashtag)}>
                              {hashtag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Generated Image */}
              {generatedContent.image && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <ImageIcon className="w-5 h-5" />
                      <span>Generated Image</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="aspect-square bg-muted rounded-lg overflow-hidden max-w-md mx-auto">
                        <img src={generatedContent.image.url} alt={generatedContent.image.alt || 'Generated image'} className="w-full h-full object-cover" loading="lazy" />
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-medium">{generatedContent.image.alt}</p>
                        <p className="text-xs text-muted-foreground">{generatedContent.image.description}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card className="h-96 flex items-center justify-center">
              <div className="text-center space-y-4">
                <MessageSquare className="w-16 h-16 mx-auto text-muted-foreground opacity-50" />
                <div>
                  <h3 className="text-lg font-medium">No Content Generated Yet</h3>
                  <p className="text-muted-foreground">
                    Fill out the form and click "Generate Post" to create your social media content
                  </p>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}