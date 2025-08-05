"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useToast } from "@/components/ui/use-toast"
import { Trash2, RefreshCw, AlertTriangle, CheckCircle, Info } from "lucide-react"

interface CleanupStats {
  cutoff_date: string
  days_old: number
  old_unapplied_jobs: number
  old_applied_jobs: number
  total_old_jobs: number
  would_be_deleted: number
}

interface CleanupResult {
  status: string
  message: string
  deleted_count: number
  cutoff_date: string
}

export function JobCleanupManager() {
  const [daysOld, setDaysOld] = useState(20)
  const [stats, setStats] = useState<CleanupStats | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [lastResult, setLastResult] = useState<CleanupResult | null>(null)
  const { toast } = useToast()

  const fetchStats = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`/api/v1/jobs/cleanup/stats?days_old=${daysOld}`)
      if (response.ok) {
        setStats(await response.json())
      } else {
        throw new Error("Failed to fetch cleanup stats")
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch cleanup statistics",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const executeCleanup = async () => {
    setIsExecuting(true)
    try {
      const response = await fetch(`/api/v1/jobs/cleanup/execute?days_old=${daysOld}`, {
        method: "POST",
      })
      
      if (response.ok) {
        const result = await response.json()
        setLastResult(result)
        
        if (result.status === "success") {
          toast({
            title: "Cleanup Successful",
            description: result.message,
            variant: "default",
          })
        } else {
          toast({
            title: "Cleanup Failed",
            description: result.message,
            variant: "destructive",
          })
        }
        
        await fetchStats()
      } else {
        throw new Error("Failed to execute cleanup")
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to execute cleanup",
        variant: "destructive",
      })
    } finally {
      setIsExecuting(false)
    }
  }

  // Load stats on component mount
  useEffect(() => {
    fetchStats()
  }, [daysOld])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trash2 className="h-5 w-5" />
            Job Cleanup Manager
          </CardTitle>
          <CardDescription>
            Automatically remove old job listings that haven't been applied to, keeping your job pool fresh and relevant.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Configuration */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Label htmlFor="days-old">Delete jobs older than:</Label>
              <Input
                id="days-old"
                type="number"
                min="1"
                max="365"
                value={daysOld}
                onChange={(e) => setDaysOld(parseInt(e.target.value) || 20)}
                className="w-20"
              />
              <span className="text-sm text-muted-foreground">days</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchStats}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
              Refresh Stats
            </Button>
          </div>

          {/* Statistics */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Would be deleted</p>
                      <p className="text-2xl font-bold text-red-600">{stats.would_be_deleted}</p>
                    </div>
                    <AlertTriangle className="h-8 w-8 text-red-500" />
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Applied jobs (kept)</p>
                      <p className="text-2xl font-bold text-green-600">{stats.old_applied_jobs}</p>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Cutoff date</p>
                      <p className="text-sm font-bold">{formatDate(stats.cutoff_date)}</p>
                    </div>
                    <Info className="h-8 w-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Warning Alert */}
          {stats && stats.would_be_deleted > 0 && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>{stats.would_be_deleted} jobs</strong> will be permanently deleted. 
                This action cannot be undone. Only jobs that haven't been applied to will be removed.
              </AlertDescription>
            </Alert>
          )}

          {/* Success Alert */}
          {stats && stats.would_be_deleted === 0 && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                No jobs need to be cleaned up. All jobs are either recent or have been applied to.
              </AlertDescription>
            </Alert>
          )}

          {/* Action Button */}
          <div className="flex justify-between items-center">
            <div className="text-sm text-muted-foreground">
              {stats && (
                <>
                  Cutoff date: <strong>{formatDate(stats.cutoff_date)}</strong> 
                  {stats.would_be_deleted > 0 && (
                    <span className="ml-2">
                      • <strong>{stats.would_be_deleted}</strong> jobs will be deleted
                    </span>
                  )}
                </>
              )}
            </div>
            
            <Button
              onClick={executeCleanup}
              disabled={isExecuting || !stats || stats.would_be_deleted === 0}
              variant="destructive"
            >
              {isExecuting ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Cleaning up...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Execute Cleanup
                </>
              )}
            </Button>
          </div>

          {/* Last Result */}
          {lastResult && (
            <Alert>
              {lastResult.status === "success" ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <AlertTriangle className="h-4 w-4" />
              )}
              <AlertDescription>
                <strong>{lastResult.status === "success" ? "Success" : "Error"}:</strong> {lastResult.message}
                {lastResult.deleted_count > 0 && (
                  <span className="ml-2">
                    <Badge variant="secondary">{lastResult.deleted_count} jobs deleted</Badge>
                  </span>
                )}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 