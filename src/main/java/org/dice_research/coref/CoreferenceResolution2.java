package org.dice_research.coref;

import com.google.common.collect.Multimap;
import com.google.common.collect.Ordering;
import com.google.common.collect.TreeMultimap;
import edu.stanford.nlp.coref.CorefCoreAnnotations;


import edu.stanford.nlp.dcoref.MentionExtractor;
import edu.stanford.nlp.dcoref.SieveCoreferenceSystem;
import edu.stanford.nlp.ling.CoreAnnotations;
import edu.stanford.nlp.ling.CoreLabel;
import edu.stanford.nlp.pipeline.Annotation;
import edu.stanford.nlp.pipeline.StanfordCoreNLP;
import edu.stanford.nlp.util.CoreMap;
import edu.stanford.nlp.util.IntPair;
import org.json.JSONObject;
import org.springframework.stereotype.Component;

import java.util.*;

/**
 * Class responsible for the Coreference Resolution
 */
@Component
public class CoreferenceResolution2 {

	// CoreNLP properties
	protected Properties props = null;
    protected SieveCoreferenceSystem corefSystem = null;
    protected MentionExtractor mentionExtractor = null;

	/**
	 * Empty constructor. Initializes the CoreNLP annotators.
	 */
	public CoreferenceResolution2() {
		props = new Properties();
        props.setProperty("annotators", "tokenize,ssplit,pos,lemma,ner,parse,coref");
        props.setProperty("coref.algorithm", "neural");

//        props.put("annotators", "tokenize, ssplit, pos, lemma, ner, parse, dcoref");

	}

	/**
	 * Escapes double quotes.
	 *
	 * @param input String to be escaped
	 * @return Escaped input string
	 */
	public static String escapeQuotes(String input) {
		return input.replace("\"", "\\\"");
	}

	/**
	 * Adds spaces to periods without spaces and replaces new lines with single
	 * spaces.
	 *
	 * @param input
	 * @return
	 */
	public static String fixErrors(String input) {
		return input.replaceAll("\\.(?!\\s)", ". ").replace("\n", " ").replace("\\n", " ");
	}

	/**
	 * Creates a JSONObject from an input string.
	 *
	 * @param input
	 * @return
	 */
	public JSONObject getJson(String input) {
		input = fixErrors(input);
		try {
			return new JSONObject(input);
		} catch (Exception e) {
			e.printStackTrace();
		}
		return null;
	}


	/**
	 * Removes square brackets from string
	 *
	 * @param input Input string
	 * @return String without starting and ending brackets
	 */
	private static String removeBrackets(String input) {
		if (input.startsWith("[") && input.endsWith("]")) {
			return input.substring(1, input.length() - 1);
		}
		return input;
	}

	/**
	 * Sorts Multimap descendingly by value
	 *
	 * @param map Map to be sorted
	 * @return Sorted Map
	 */
	private static Multimap<Integer, String> sortByValueDescending(Map<String, List<Object>> map) {

		// Create a TreeMultimap to store the reordered data
		Multimap<Integer, String> reorderedMultimap = TreeMultimap.create((o1, o2) -> Integer.compare(o1, o2),
				Ordering.natural());

		// Iterate through the original map and populate the multimap
		for (Map.Entry<String, List<Object>> entry : map.entrySet()) {
			String key = entry.getKey();
			List<Object> values = entry.getValue();

			for (Object value : values) {
				reorderedMultimap.put((Integer) value, key);
			}
		}
		return reorderedMultimap;
	}

	/**
	 * Does coref resolution and then, replaces the mentions with the corefer'd
	 * version.
	 *
	 * @param input String to annotate
	 * @return Coreferenced input
	 */
	public String generateCrR(String input) {
		// pipeline is here instead of a class-level attribute to prevent OOMs

		Annotation document = new Annotation(input);
		StanfordCoreNLP pipeline = new StanfordCoreNLP(props);
		pipeline.annotate(document);

		// Replace pronouns and noun phrases with their most typical mentions
		return replaceCoreferences(input, document);
	}

	/**
	 * Generates the coreferenced text by replacing the coreferenced spans in the
	 * document.
	 *
	 * @param text     Input text
	 * @param document Annotated document
	 * @return
	 */
    public String replaceCoreferences(String text, Annotation document) {

        // Get coreference chains
        Map<Integer, edu.stanford.nlp.coref.data.CorefChain> corefChains = document.get(CorefCoreAnnotations.CorefChainAnnotation.class);
        Map<IntPair, String> replacements = new HashMap<>();

        Set<String> possessivePronouns = new HashSet<>(Arrays.asList("his", "her", "its", "their", "our", "my", "your"));

        // Build a map of (sentNum, startIndex) -> replacement text
        if (corefChains != null) {

            for (edu.stanford.nlp.coref.data.CorefChain chain : corefChains.values()) {
                edu.stanford.nlp.coref.data.CorefChain.CorefMention representative = chain.getRepresentativeMention();
                String representativeText = representative.mentionSpan;

                for (edu.stanford.nlp.coref.data.CorefChain.CorefMention mention : chain.getMentionsInTextualOrder()) {
                    if (mention == representative) continue;

                    // Only replace pronominal mentions
                    if ("PRONOMINAL".equalsIgnoreCase(mention.mentionType.toString())) {
                        IntPair key = new IntPair(mention.sentNum, mention.startIndex);

                        // Detect possessive pronoun
                        String original = mention.mentionSpan.toLowerCase();
                        String replacement = possessivePronouns.contains(original)
                                ? representativeText + "'s"
                                : representativeText;

                        replacements.put(key, replacement);

                        // Optional: you can skip filling other tokens of the span if multi-word (if needed)
                        // Currently, we assume single-token pronouns
                    }
                }
            }
        }

        // Reconstruct the text with replacements
        List<CoreMap> sentences = document.get(CoreAnnotations.SentencesAnnotation.class);
        StringBuilder resolvedText = new StringBuilder();

        for (int i = 0; i < sentences.size(); i++) {
            CoreMap sentence = sentences.get(i);
            List<CoreLabel> tokens = sentence.get(CoreAnnotations.TokensAnnotation.class);

            for (int j = 0; j < tokens.size(); j++) {
                CoreLabel token = tokens.get(j);
                IntPair key = new IntPair(i + 1, j + 1); // 1-based indexing

                String word = replacements.getOrDefault(key, token.word());
                resolvedText.append(word).append(" ");
            }
        }

        // Clean up extra spaces and punctuation spacing
        String cleanedText = resolvedText.toString()
                .replaceAll("\\s+([.,!?;:])", "$1")  // space before punctuation
                .replaceAll("\\s+", " ")            // multiple spaces
                .trim();

        System.out.println("\n--- Original Text ---\n" + text);
        System.out.println("\n--- Resolved Text ---\n" + cleanedText);

        return cleanedText;
    }
//
//    public String replaceCoreferences(String text, Annotation document) {
//
//
//        // Get coreference chains
//        Map<Integer, edu.stanford.nlp.coref.data.CorefChain> corefChains = document.get(CorefCoreAnnotations.CorefChainAnnotation.class);
////        Map<Integer, CorefChain> corefChains = document.get(CorefChainAnnotation.class);
//
//        // Build a mapping from position to replacement text
//        Map<IntPair, String> replacements = new HashMap<>();
//        for (edu.stanford.nlp.coref.data.CorefChain chain : corefChains.values()) {
//            edu.stanford.nlp.coref.data.CorefChain.CorefMention representative = chain.getRepresentativeMention();
//            String representativeText = representative.mentionSpan;
//
//            for (edu.stanford.nlp.coref.data.CorefChain.CorefMention mention : chain.getMentionsInTextualOrder()) {
//                if (mention == representative) continue;
//
//                // Only replace pronominal mentions (as string comparison)
//                if ("PRONOMINAL".equalsIgnoreCase((mention.mentionType).toString())) {
//                    IntPair key = new IntPair(mention.sentNum, mention.startIndex);
//                    replacements.put(key, representative.mentionSpan);
//                }
//            }
//
//        }
//
//        // Reconstruct the text with pronouns replaced
//        List<CoreMap> sentences = document.get(CoreAnnotations.SentencesAnnotation.class);
//        StringBuilder resolvedText = new StringBuilder();
//
//        for (int i = 0; i < sentences.size(); i++) {
//            CoreMap sentence = sentences.get(i);
//            List<CoreLabel> tokens = sentence.get(CoreAnnotations.TokensAnnotation.class);
//
//            for (int j = 0; j < tokens.size(); j++) {
//                CoreLabel token = tokens.get(j);
//                IntPair key = new IntPair(i + 1, j + 1); // 1-based indexing
//
//                if (replacements.containsKey(key)) {
//                    resolvedText.append(replacements.get(key)).append(" ");
//                } else {
//                    resolvedText.append(token.word()).append(" ");
//                }
//            }
//        }
//
//        System.out.println("\n--- Original Text ---\n");
//        System.out.println(text);
//
//        System.out.println("\n--- Text after Pronoun Resolution ---\n");
//        System.out.println(resolvedText.toString().trim());
//
//        String cleanedText = resolvedText.toString()
//                .replaceAll("\\s+([.,!?;:])", "$1")
//                .replaceAll("\\s+", " ")
//                .trim();
//
//        System.out.println("\n--- Cleaned Text after Pronoun Resolution ---\n");
//        System.out.println(cleanedText);
//
//
//        String para = cleanedText;
//		return para;
//	}
}
