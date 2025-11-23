"use client"

import React, { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { X, Plus, ChevronDown } from "lucide-react"
import { searchSkills, getPopularSkills, type SkillDatabase } from "@/lib/skills-database"

interface SkillsAutocompleteProps {
  category: keyof SkillDatabase
  value: string[]
  onChange: (skills: string[]) => void
  placeholder?: string
  maxSkills?: number
  label?: string
}

export function SkillsAutocomplete({
  category,
  value = [],
  onChange,
  placeholder = "Add skills...",
  maxSkills = 20,
  label
}: SkillsAutocompleteProps) {
  const [inputValue, setInputValue] = useState("")
  const [isOpen, setIsOpen] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  // Update suggestions when input changes
  useEffect(() => {
    if (inputValue.trim()) {
      const results = searchSkills(inputValue, category, 10)
      // Filter out already selected skills
      const filteredResults = results.filter(skill => !value.includes(skill))
      setSuggestions(filteredResults)
    } else {
      // Show popular skills when no input
      const popular = getPopularSkills(category, 10)
      const filteredPopular = popular.filter(skill => !value.includes(skill))
      setSuggestions(filteredPopular)
    }
  }, [inputValue, value, category])

  const addSkill = (skill: string) => {
    if (!skill.trim()) return

    const trimmedSkill = skill.trim()

    // Don't add if already exists or max reached
    if (value.includes(trimmedSkill) || value.length >= maxSkills) return

    onChange([...value, trimmedSkill])
    setInputValue("")
    setIsOpen(false)
  }

  const removeSkill = (skillToRemove: string) => {
    onChange(value.filter(skill => skill !== skillToRemove))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      if (inputValue.trim()) {
        addSkill(inputValue)
      }
    } else if (e.key === "Backspace" && !inputValue && value.length > 0) {
      // Remove last skill when backspace on empty input
      removeSkill(value[value.length - 1])
    } else if (e.key === "Escape") {
      setIsOpen(false)
      inputRef.current?.blur()
    }
  }

  const handleInputChange = (newValue: string) => {
    setInputValue(newValue)
    if (newValue.trim()) {
      setIsOpen(true)
    }
  }

  return (
    <div className="space-y-2">
      {label && <label className="text-sm font-medium text-gray-700">{label}</label>}

      {/* Selected Skills */}
      {value.length > 0 && (
        <div className="flex flex-wrap gap-2 p-2 border rounded-md bg-gray-50 min-h-[40px]">
          {value.map((skill) => (
            <Badge
              key={skill}
              variant="secondary"
              className="flex items-center gap-1 bg-blue-100 text-blue-800 hover:bg-blue-200"
            >
              {skill}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeSkill(skill)}
                className="h-4 w-4 p-0 hover:bg-blue-300 rounded-full"
              >
                <X className="h-3 w-3" />
              </Button>
            </Badge>
          ))}
          {value.length >= maxSkills && (
            <span className="text-xs text-gray-500 self-center">
              Maximum {maxSkills} skills reached
            </span>
          )}
        </div>
      )}

      {/* Add New Skill */}
      {value.length < maxSkills && (
        <Popover open={isOpen} onOpenChange={setIsOpen}>
          <PopoverTrigger asChild>
            <div className="relative">
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => handleInputChange(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setIsOpen(true)}
                placeholder={placeholder}
                className="pr-8"
              />
              <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            </div>
          </PopoverTrigger>

          <PopoverContent className="w-full p-0" align="start">
            <Command>
              <CommandList>
                {suggestions.length === 0 ? (
                  <CommandEmpty>
                    {inputValue ? (
                      <div className="p-2">
                        <p className="text-sm text-gray-600">No matches found.</p>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => addSkill(inputValue)}
                          className="w-full justify-start mt-2"
                        >
                          <Plus className="h-4 w-4 mr-2" />
                          Add "{inputValue}"
                        </Button>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-600">Start typing to see suggestions</p>
                    )}
                  </CommandEmpty>
                ) : (
                  <CommandGroup>
                    {suggestions.map((skill) => (
                      <CommandItem
                        key={skill}
                        value={skill}
                        onSelect={() => addSkill(skill)}
                        className="cursor-pointer"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        {skill}
                      </CommandItem>
                    ))}

                    {/* Option to add custom skill if not in suggestions */}
                    {inputValue && !suggestions.includes(inputValue) && (
                      <CommandItem
                        value={inputValue}
                        onSelect={() => addSkill(inputValue)}
                        className="cursor-pointer border-t"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Add "{inputValue}"
                      </CommandItem>
                    )}
                  </CommandGroup>
                )}
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>
      )}

      {/* Help text */}
      <p className="text-xs text-gray-500">
        Type to search or add custom skills. Press Enter to add. ({value.length}/{maxSkills})
      </p>
    </div>
  )
}