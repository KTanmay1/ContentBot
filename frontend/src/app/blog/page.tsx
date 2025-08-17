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
  FileText,
  Wand2,
  Clock,
  CheckCircle,
  AlertCircle,
  Image as ImageIcon,
  Copy,
  Download,
  Eye,
  Sparkles
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api'

interface BlogFormData {
  topic: string
  audience: string
  tone: string
  length: string
  keywords: string
  includeImages: boolean
  seoOptimized: boolean
  llmModel: string
}

export default function BlogGenerator() {
  const { createWorkflow, activeWorkflow } = useAppStore()
  const [formData, setFormData] = useState<BlogFormData>({
    topic: '',
    audience: 'general',
    tone: 'professional',
    length: 'medium',
    keywords: '',
    includeImages: true,
    seoOptimized: true,
    llmModel: 'mistral'
  })
  const [generatedContent, setGeneratedContent] = useState<any>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const handleInputChange = (field: keyof BlogFormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleGenerate = async () => {
    if (!formData.topic.trim()) {
      alert('Please enter a topic for your blog post')
      return
    }

    setIsGenerating(true)
    setGeneratedContent(null)

    try {
      const inputData = {
        text: formData.topic,
        topic: formData.topic,
        audience: formData.audience,
        tone: formData.tone,
        length: formData.length,
        keywords: formData.keywords.split(',').map(k => k.trim()).filter(k => k),
        include_images: formData.includeImages,
        seo_optimized: formData.seoOptimized,
        llm_model: formData.llmModel
      }

      const workflowId = await createWorkflow('blog_generation', inputData)
      
      // Poll for workflow completion
      const pollInterval = setInterval(async () => {
        try {
          const status = await apiClient.getWorkflowStatus(workflowId)
          
          if (status.status === 'completed') {
            clearInterval(pollInterval)
            const result = await apiClient.getWorkflowResult(workflowId)
            
            // Transform backend result to frontend format (ensure we never pass objects to React)
            const tc = result?.text_content
            let textContent: string = 'Content generation completed.'
            if (typeof tc === 'string') {
              textContent = tc
            } else if (tc && typeof tc.generated === 'string') {
              textContent = tc.generated
            }
            const wordCount = textContent.split(' ').filter(Boolean).length
            
            setGeneratedContent({
              title: `Blog Post: ${formData.topic}`,
              content: textContent,
              keywords: formData.keywords.split(',').map(k => k.trim()).filter(k => k),
              wordCount: wordCount,
              readingTime: Math.ceil(wordCount / 200),
              seoScore: result.quality_scores?.seo_score || 0,
              images: (result.image_content && typeof result.image_content.generated === 'string')
                ? [{
                    url: result.image_content.generated,
                    alt: `Image for ${formData.topic}`,
                    caption: `Auto-generated visual for "${formData.topic}"`
                  }]
                : []
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
      console.error('Failed to generate blog post:', error)
      setIsGenerating(false)
      alert('Failed to generate content. Please try again.')
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // You could add a toast notification here
  }

  const downloadContent = () => {
    if (!generatedContent) return
    
    const element = document.createElement('a')
    const file = new Blob([generatedContent.content], { type: 'text/markdown' })
    element.href = URL.createObjectURL(file)
    element.download = `${generatedContent.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-2xl mb-4">
            <FileText className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
            AI Blog Generator
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Transform your ideas into engaging, SEO-optimized blog posts with the power of AI
          </p>
        </div>
        {activeWorkflow && activeWorkflow.type === 'blog_generation' && (
          <div className="mx-auto max-w-md">
            <div className="bg-primary/5 border border-primary/20 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-center space-x-2">
                <div className="w-3 h-3 bg-primary rounded-full animate-pulse" />
                <span className="text-sm font-medium text-primary">AI is crafting your content...</span>
              </div>
              <Progress value={activeWorkflow.progress} className="w-full h-2" />
              <p className="text-xs text-center text-muted-foreground">
                {activeWorkflow.progress}% complete
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-5 gap-8">
          {/* Input Form */}
          <div className="xl:col-span-2 space-y-6">
          <Card className="shadow-xl border-0 bg-card/50 backdrop-blur-sm">
            <CardHeader className="bg-gradient-to-r from-primary/5 to-primary/10 rounded-t-lg">
              <CardTitle className="flex items-center space-x-2 text-xl">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Wand2 className="w-5 h-5 text-primary" />
                </div>
                <span>Blog Configuration</span>
              </CardTitle>
              <CardDescription className="text-base">
                Configure your blog post parameters to generate the perfect content
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 p-6">
              {/* Topic */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-foreground flex items-center space-x-2">
                  <span>Topic</span>
                  <span className="text-destructive">*</span>
                </label>
                <Input
                  placeholder="e.g., 'The Future of Artificial Intelligence in Healthcare'"
                  value={formData.topic}
                  onChange={(e) => handleInputChange('topic', e.target.value)}
                  className="w-full h-12 text-base border-2 focus:border-primary transition-colors"
                />
              </div>

              {/* Audience */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Target Audience</label>
                <Select value={formData.audience} onValueChange={(value) => handleInputChange('audience', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General Audience</SelectItem>
                    <SelectItem value="beginners">Beginners</SelectItem>
                    <SelectItem value="intermediate">Intermediate</SelectItem>
                    <SelectItem value="experts">Experts</SelectItem>
                    <SelectItem value="professionals">Professionals</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Tone */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Writing Tone</label>
                <Select value={formData.tone} onValueChange={(value) => handleInputChange('tone', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="casual">Casual</SelectItem>
                    <SelectItem value="friendly">Friendly</SelectItem>
                    <SelectItem value="authoritative">Authoritative</SelectItem>
                    <SelectItem value="conversational">Conversational</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Length */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Article Length</label>
                <Select value={formData.length} onValueChange={(value) => handleInputChange('length', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="short">Short (500-800 words)</SelectItem>
                    <SelectItem value="medium">Medium (800-1500 words)</SelectItem>
                    <SelectItem value="long">Long (1500-2500 words)</SelectItem>
                    <SelectItem value="comprehensive">Comprehensive (2500+ words)</SelectItem>
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

              {/* Keywords */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Keywords (optional)</label>
                <Textarea
                  placeholder="Enter keywords separated by commas..."
                  value={formData.keywords}
                  onChange={(e) => handleInputChange('keywords', e.target.value)}
                  className="min-h-[80px]"
                />
              </div>

              {/* Options */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Include Images</label>
                  <input
                    type="checkbox"
                    checked={formData.includeImages}
                    onChange={(e) => handleInputChange('includeImages', e.target.checked)}
                    className="rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">SEO Optimized</label>
                  <input
                    type="checkbox"
                    checked={formData.seoOptimized}
                    onChange={(e) => handleInputChange('seoOptimized', e.target.checked)}
                    className="rounded"
                  />
                </div>
              </div>

              {/* Generate Button */}
              <div className="pt-4 border-t border-border/50">
                <Button
                  onClick={handleGenerate}
                  disabled={isGenerating || !formData.topic.trim()}
                  className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-primary to-primary/90 hover:from-primary/90 hover:to-primary shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-[1.02]"
                  size="lg"
                >
                  {isGenerating ? (
                    <>
                      <Clock className="w-5 h-5 mr-3 animate-spin" />
                      <span>Crafting Your Content...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5 mr-3" />
                      <span>Generate Blog Post</span>
                    </>
                  )}
                </Button>
                <p className="text-xs text-muted-foreground text-center mt-2">
                  Powered by {formData.llmModel === 'mistral' ? 'Mistral AI' : 'Gemini'}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

          {/* Generated Content */}
          <div className="xl:col-span-3 space-y-6">
          {generatedContent ? (
            <>
              {/* Content Header */}
              <Card className="shadow-xl border-0 bg-card/50 backdrop-blur-sm">
                <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 rounded-t-lg">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center space-x-3 text-xl">
                      <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                        <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                      </div>
                      <span>Content Generated Successfully</span>
                    </CardTitle>
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(generatedContent.content)}
                      >
                        <Copy className="w-4 h-4 mr-2" />
                        Copy
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={downloadContent}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">{generatedContent.wordCount}</div>
                      <div className="text-sm text-muted-foreground">Words</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">{generatedContent.readingTime}</div>
                      <div className="text-sm text-muted-foreground">Min Read</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">{generatedContent.seoScore}</div>
                      <div className="text-sm text-muted-foreground">SEO Score</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">{generatedContent.images.length}</div>
                      <div className="text-sm text-muted-foreground">Images</div>
                    </div>
                  </div>
                  
                  {generatedContent.keywords.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium mb-2">Keywords:</h4>
                      <div className="flex flex-wrap gap-2">
                        {generatedContent.keywords.map((keyword: string, index: number) => (
                          <Badge key={index} variant="secondary">{keyword}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Content Preview */}
              <Card className="shadow-xl border-0 bg-card/50 backdrop-blur-sm">
                <CardHeader className="bg-gradient-to-r from-primary/5 to-primary/10 rounded-t-lg">
                  <CardTitle className="flex items-center space-x-2 text-xl">
                    <Eye className="w-5 h-5 text-primary" />
                    <span>Content Preview</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-8">
                  <div className="prose prose-lg max-w-none dark:prose-invert prose-headings:text-foreground prose-p:text-muted-foreground prose-strong:text-foreground">
                    <h1 className="text-3xl font-bold mb-6 text-foreground">{generatedContent.title}</h1>
                    <div className="whitespace-pre-wrap leading-relaxed text-base">
                      {generatedContent.content}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Images */}
              {generatedContent.images.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <ImageIcon className="w-5 h-5" />
                      <span>Generated Images</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {generatedContent.images.map((image: any, index: number) => (
                        <div key={index} className="space-y-2">
                          <div className="aspect-video bg-muted rounded-lg overflow-hidden">
                            <img src={image.url} alt={image.alt || 'Generated image'} className="w-full h-full object-cover" loading="lazy" />
                          </div>
                          <div>
                            <p className="text-sm font-medium">{image.alt}</p>
                            <p className="text-xs text-muted-foreground">{image.caption}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card className="h-96 flex items-center justify-center">
              <div className="text-center space-y-4">
                <FileText className="w-16 h-16 mx-auto text-muted-foreground opacity-50" />
                <div>
                  <h3 className="text-lg font-medium">No Content Generated Yet</h3>
                  <p className="text-muted-foreground">
                    Fill out the form and click "Generate Blog Post" to create your content
                  </p>
                </div>
              </div>
            </Card>
          )}
          </div>
        </div>
      </div>
    </div>
  )
}