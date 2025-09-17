package org.dice_research.coref;

import edu.stanford.nlp.pipeline.StanfordCoreNLP;
import org.dice_research.coref.CoreferenceResolution;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class CoreferenceResolutionTest {

    private CoreferenceResolution2 coreferenceResolution;

    @BeforeEach
    public void setUp() {
        coreferenceResolution = new CoreferenceResolution2();
    }

    @Test
    public void testEscapeQuotes() {
        String input = "He said, \"Hello!\"";
        String expected = "He said, \\\"Hello!\\\"";
        String result = CoreferenceResolution.escapeQuotes(input);
        assertEquals(expected, result);
    }

    @Test
    public void testFixErrors() {
        String input = "Hello.There\nHow are you?";
        String expected = "Hello. There How are you?";
        String result = CoreferenceResolution.fixErrors(input);
        assertEquals(expected, result);
    }

    @Test
    public void testCoreferenceResolutionSimple() {
        String input = "Barack Obama was born in Hawaii. He is a former president.";
        String expected = "Barack Obama was born in Hawaii. Barack Obama is a former president."; // Expected behavior
        String result = coreferenceResolution.generateCrR(input);
        assertEquals(expected, result);
    }

    @Test
    public void testCoreferenceResolutionComplex() {
        String input = "Michelle Obama was born in Chicago. She married Barack Obama.";
        String expected = "Michelle Obama was born in Chicago. Michelle Obama married Barack Obama."; // Expected behavior
        String result = coreferenceResolution.generateCrR(input);
        assertEquals(expected, result);
    }

    @Test
    public void testCoreferenceResolution_AlbertEinstein() {
        String input = "Albert Einstein was one of the most brilliant physicists in history. "
                + "He developed the theory of relativity. "
                + "His work revolutionized physics. "
                + "Einstein received the Nobel Prize in 1921. "
                + "He is still remembered for his intelligence and curiosity.";

        String expected = "Albert Einstein was one of the most brilliant physicists in history. "
                + "Albert Einstein developed the theory of relativity. "
                + "Albert Einstein's work revolutionized physics. "
                + "Einstein received the Nobel Prize in 1921. "
                + "Albert Einstein is still remembered for Albert Einstein's intelligence and curiosity.";

        String result = coreferenceResolution.generateCrR(input);
        assertEquals(expected, result);
    }

    // Add more test cases as needed to cover edge cases, multiple sentences, and so on
}