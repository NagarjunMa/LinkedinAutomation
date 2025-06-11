"use client";

import React from "react";
import {
    SimpleGrid,
    Box,
    Heading,
    Text,
    Flex,
    Badge,
    IconButton,
    VStack,
} from "@chakra-ui/react";
import { ExternalLink, Bookmark, Share2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { fetchJobs } from "../lib/api";

type Job = {
    id: number;
    title: string;
    company: string;
    location: string;
    type: string;
    description: string;
    url: string;
    postedAt: string;
    salary?: string;
    experience?: string;
    skills?: string[];
};

export function JobList() {
    const { data: jobs, isLoading } = useQuery<Job[]>({
        queryKey: ["jobs"],
        queryFn: fetchJobs,
    });

    // Color palette matching your screenshot
    const darkBg = "#11212D";
    const lightBg = "#F7F9FA";
    const cardBg = darkBg;
    const borderColor = "#253745";
    const titleColor = "#CCD0CF";
    const companyColor = "#9BA8AB";
    const badgeBg = "#9BA8AB";
    const badgeText = "#06141B";
    const postedColor = "#4A5C6A";
    const descriptionColor = "#CCD0CF";
    const iconColor = "#CCD0CF";
    const iconHoverBg = "#253745";
    const iconHoverColor = "#9BA8AB";

    if (isLoading) {
        return (
            <Box w="100%" p={8} bg={darkBg} minH="100vh">
                <Text color={titleColor} textAlign="center">Loading jobs...</Text>
            </Box>
        );
    }

    return (
        <Box
            w="100%"
            minH="60vh"
            bg={darkBg}
            py={12}
            px={0}
        >
            <Heading
                as="h2"
                size="6xl"
                mb={8}
                textAlign="center"
                color={titleColor}
            >
                Job Listings
            </Heading>

            <SimpleGrid
                columns={{ base: 1, sm: 2, lg: 3, xl: 4 }}
                gap={6}
                w="100%"
                maxW="none"
                px={{ base: 4, md: 6, lg: 8 }}
            >
                {jobs?.map((job) => (
                    <Box
                        key={job.id}
                        bg={cardBg}
                        borderRadius="xl"
                        boxShadow="lg"
                        borderWidth="1px"
                        borderColor={borderColor}
                        p={6}
                        display="flex"
                        flexDirection="column"
                        justifyContent="space-between"
                        minH="320px"
                        maxW="300px"
                        _hover={{
                            boxShadow: "2xl",
                            transform: "translateY(-4px)",
                            transition: "all 0.2s ease-in-out"
                        }}
                    >
                        <VStack gap={3} align="stretch" flex="1">
                            <Heading as="h3" size="xl" color={titleColor}>
                                {job.title}
                            </Heading>

                            <Text fontSize="sm" color={companyColor} fontWeight="medium">
                                {job.company}
                            </Text>

                            {/* Center-aligned company logo/indicator */}
                            <Flex wrap="wrap" gap={2}>
                                <Badge bg={badgeBg} color={badgeText} borderRadius="full" px={3} py={1}>
                                    {job.type}
                                </Badge>
                                <Badge
                                    variant="outline"
                                    color={badgeBg}
                                    borderColor={badgeBg}
                                    borderRadius="full"
                                    px={3}
                                    py={1}
                                    maxW="120px"
                                    overflow="hidden"
                                    textOverflow="ellipsis"
                                    whiteSpace="nowrap"
                                >
                                    {job.location}
                                </Badge>
                                {job.salary && (
                                    <Badge
                                        variant="outline"
                                        color={badgeBg}
                                        borderColor={badgeBg}
                                        borderRadius="full"
                                        px={3}
                                        py={1}
                                        maxW="100px"
                                        overflow="hidden"
                                        textOverflow="ellipsis"
                                        whiteSpace="nowrap"
                                    >
                                        {job.salary}
                                    </Badge>
                                )}
                            </Flex>

                            {job.skills && job.skills.length > 0 && (
                                <Flex wrap="wrap" gap={2}>
                                    {job.skills.slice(0, 5).map((skill) => (
                                        <Badge
                                            key={skill}
                                            bg={badgeBg}
                                            color={badgeText}
                                            borderRadius="full"
                                            px={2}
                                            py={1}
                                            fontSize="xs"
                                        >
                                            {skill}
                                        </Badge>
                                    ))}
                                    {job.skills.length > 5 && (
                                        <Badge
                                            bg={badgeBg}
                                            color={badgeText}
                                            borderRadius="full"
                                            px={2}
                                            py={1}
                                            fontSize="xs"
                                        >
                                            +{job.skills.length - 5}
                                        </Badge>
                                    )}
                                </Flex>
                            )}

                            <Text fontSize="xs" color={postedColor} fontWeight="medium">
                                {job.postedAt && !isNaN(new Date(job.postedAt).getTime())
                                    ? `Posted ${format(new Date(job.postedAt), "MMM d, yyyy")}`
                                    : "Posted date unknown"}
                            </Text>

                            <Text
                                fontSize="sm"
                                color={descriptionColor}
                                flex="1"
                            >
                                {job.description.length > 150
                                    ? `${job.description.substring(0, 150)}...`
                                    : job.description
                                }
                            </Text>
                        </VStack>

                        <Flex justify="flex-end" gap={2} mt={4} pt={4} borderTop="1px" borderColor={borderColor}>
                            <IconButton
                                aria-label="Open job"
                                color={iconColor}
                                variant="ghost"
                                onClick={() => window.open(job.url, "_blank")}
                                _hover={{ bg: iconHoverBg, color: iconHoverColor }}
                                size="sm"
                            >
                                <ExternalLink size={16} />
                            </IconButton>
                            <IconButton
                                aria-label="Bookmark"
                                color={iconColor}
                                variant="ghost"
                                _hover={{ bg: iconHoverBg, color: iconHoverColor }}
                                size="sm"
                            >
                                <Bookmark size={16} />
                            </IconButton>
                            <IconButton
                                aria-label="Share"
                                color={iconColor}
                                variant="ghost"
                                _hover={{ bg: iconHoverBg, color: iconHoverColor }}
                                size="sm"
                            >
                                <Share2 size={16} />
                            </IconButton>
                        </Flex>
                    </Box>
                ))}
            </SimpleGrid>
        </Box>
    );
} 