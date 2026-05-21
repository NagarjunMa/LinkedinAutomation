"use client"

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Clock } from "lucide-react"

interface HistoryTabProps {
    userId: string
}

function HistoryTab({ userId: _userId }: HistoryTabProps) {
    const [history] = useState([
        {
            id: 1,
            action: 'Profile Updated',
            timestamp: '2025-01-27 10:30:00',
            details: 'Updated target role and job preferences'
        },
        {
            id: 2,
            action: 'Privacy Settings Updated',
            timestamp: '2025-01-26 15:45:00',
            details: 'Updated data retention preference'
        },
        {
            id: 3,
            action: 'Resume Uploaded',
            timestamp: '2025-01-25 09:15:00',
            details: 'resume.pdf uploaded and evaluated'
        }
    ])

    return (
        <div className="space-y-6">
            <Card className="premium-card bg-card border-border">
                <CardHeader>
                    <CardTitle className="text-foreground flex items-center gap-2">
                        <Clock className="h-5 w-5" />
                        Change History
                    </CardTitle>
                    <CardDescription className="text-muted-foreground">
                        Track all changes made to your account
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {history.map((item) => (
                        <div key={item.id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                            <div>
                                <div className="text-foreground font-medium">{item.action}</div>
                                <div className="text-sm text-muted-foreground">{item.details}</div>
                            </div>
                            <div className="text-sm text-muted-foreground">
                                {item.timestamp}
                            </div>
                        </div>
                    ))}

                    <div className="pt-4">
                        <Button variant="outline" className="border-border text-foreground hover:bg-muted">
                            Export History
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

export default HistoryTab