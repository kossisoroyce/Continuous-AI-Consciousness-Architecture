/**
 * Experiential Layer Test Protocol - Automated Test Sequences
 */

export const EXPERIENTIAL_TEST_PROTOCOL = {
    name: "Experiential Layer Validation",
    description: "Validation of memory, facts, commitments, and user state tracking.",
    experiments: [
        {
            id: "exp_memory_facts",
            name: "Experiment A: Salient Fact Extraction",
            description: "Verify that the system extracts and stores facts about the user.",
            expectedResults: "New entries in 'Salient Facts' panel.",
            prompts: [
                "My name is Kossiso.",
                "I am a software engineer working on an AI architecture project.",
                "I live in Accra, Ghana.",
                "I prefer using Python for backend development."
            ]
        },
        {
            id: "exp_memory_recall",
            name: "Experiment B: Fact Recall & Context integration",
            description: "Verify that the system can answer questions based on previously stated facts.",
            expectedResults: "Correct answers citing earlier facts.",
            prompts: [
                "What is my name?",
                "Where did I say I live?",
                "What programming language do I prefer?",
                "What kind of project am I working on?"
            ]
        },
        {
            id: "exp_commitments",
            name: "Experiment C: Commitment Tracking",
            description: "Verify that promises and tasks are tracked as commitments.",
            expectedResults: "New entries in 'Commitments' panel.",
            prompts: [
                "Remind me to push the code to git later.",
                "Can you help me write a test script? Promise you'll check it for errors.",
                "I need you to remember to ask me about my day at the end of this session."
            ]
        },
        {
            id: "exp_topic_shift",
            name: "Experiment D: Topic & Emotion Tracking",
            description: "Verify that the conversation model tracks topic shifts and emotional trajectory.",
            expectedResults: "Topic summary updates; emotion summary updates.",
            prompts: [
                "Let's change the subject. I want to talk about cooking.",
                "I'm feeling really happy today because my code finally worked!",
                "Actually, I'm getting frustrated. This pasta recipe is too hard.",
                "Never mind, let's go back to discussing AI architectures."
            ]
        }
    ]
};

// Get flat list of all prompts with metadata
export const getAllExperientialPrompts = () => {
    const prompts = [];
    EXPERIENTIAL_TEST_PROTOCOL.experiments.forEach(exp => {
        exp.prompts.forEach((prompt, idx) => {
            prompts.push({
                experimentId: exp.id,
                experimentName: exp.name,
                promptIndex: idx + 1,
                totalInExperiment: exp.prompts.length,
                prompt: prompt
            });
        });
    });
    return prompts;
};
