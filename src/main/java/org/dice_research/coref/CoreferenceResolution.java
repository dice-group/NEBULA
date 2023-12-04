package org.dice_research.coref;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Properties;

import org.json.JSONObject;

import com.google.common.collect.Multimap;
import com.google.common.collect.Ordering;
import com.google.common.collect.TreeMultimap;

import edu.stanford.nlp.coref.CorefCoreAnnotations;
import edu.stanford.nlp.coref.data.CorefChain;
import edu.stanford.nlp.ling.CoreAnnotations;
import edu.stanford.nlp.ling.CoreLabel;
import edu.stanford.nlp.pipeline.Annotation;
import edu.stanford.nlp.pipeline.StanfordCoreNLP;
import edu.stanford.nlp.util.CoreMap;

/**
 * Class responsible for the Coreference Resolution
 */
public class CoreferenceResolution {

	// CoreNLP properties
	protected Properties props = null;

	/**
	 * Empty constructor. Initializes the CoreNLP annotators.
	 */
	public CoreferenceResolution() {
		props = new Properties();
		props.setProperty("annotators", "tokenize,ssplit,pos,lemma,ner,parse,dcoref");
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
	 * Replaces mentions with the coreferenced equivalents.
	 * 
	 * @param sentence     Input document
	 * @param corefChains  Coreferences
	 * @param document     Annotated document
	 * @param sentence_num Number of sentences
	 * @return Coreferenced input sentence
	 */
	private String replaceMentions(CoreMap sentence, Map<Integer, CorefChain> corefChains, Annotation document,
			Integer sentence_num) {
		// Create a copy of the original sentence text
		String modifiedSentence = sentence.toString();
		int start_index = 0;
		int end_index = 0;
		HashMap<String, List<Object>> corefs = new HashMap<>();
		HashMap<String, List<Object>> start_coref = new HashMap<>();
		HashMap<String, List<Object>> end_coref = new HashMap<>();
		HashMap<String, List<Object>> mentionSpan = new HashMap<>();
		for (CorefChain corefChain : corefChains.values()) {
			if (((HashSet) (corefChain.getMentionMap().values()).toArray()[0]).size() > 1) {
				for (Object coref1 : ((HashSet) (corefChain.getMentionMap().values()).toArray()[0])) {
					CorefChain.CorefMention representativeMention = corefChain.getRepresentativeMention();
					if (coref1 == representativeMention) {
						// mentionSpan.add(representativeMention.mentionSpan);
					} else {
						if (((CorefChain.CorefMention) coref1).sentNum == sentence_num + 1) {
							start_index = ((CorefChain.CorefMention) coref1).startIndex;
							end_index = ((CorefChain.CorefMention) coref1).endIndex;
							addIntegerToMap(mentionSpan, representativeMention.mentionSpan,
									representativeMention.mentionSpan);
							addIntegerToMap(start_coref, representativeMention.mentionSpan, start_index);
							addIntegerToMap(end_coref, representativeMention.mentionSpan, end_index);
							addIntegerToMap(corefs, representativeMention.mentionSpan, coref1);
						}
					}
				}
			}
		}

		if (corefs.size() > 0) {
			modifiedSentence = replaceSubstring(corefs, start_coref, end_coref, sentence);
		}
		return modifiedSentence;
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
	 * Adds integer to a list in map values if key is existing, otherwise creates it
	 * 
	 * @param map   Map to add to
	 * @param key   Map key
	 * @param value Map value - The integer
	 */
	private static void addIntegerToMap(Map<String, List<Object>> map, String key, Object value) {
		// If the key exists in the map, add the value to the existing list
		if (map.containsKey(key)) {
			map.get(key).add(value);
		} else {
			// If the key doesn't exist, create a new list, add the value, and put it in the
			// map
			List<Object> newList = new ArrayList<>();
			newList.add(value);
			map.put(key, newList);
		}
	}

	/**
	 * Replaces substrings
	 * 
	 * @param corefs
	 * @param startIndex
	 * @param endIndex
	 * @param document
	 * @return
	 */
	private static String replaceSubstring(HashMap<String, List<Object>> corefs,
			HashMap<String, List<Object>> startIndex, HashMap<String, List<Object>> endIndex, CoreMap document) {
		List<String> parts = new ArrayList<>();// original.split("(?=\\W)");
		int ii = 0;
		for (CoreLabel label : document.get(CoreAnnotations.TokensAnnotation.class)) {
			parts.add(label.value().toString());
		}
		Multimap reps_start = sortByValueDescending(startIndex);
		Multimap reps_end = sortByValueDescending(endIndex);
		String final_res = "";

		// Create an iterator for each list
		Iterator<Object> iterator1 = reps_start.keySet().iterator();
		Iterator<Object> iterator2 = reps_end.keySet().iterator();
		// Iterate through both lists simultaneously using a foreach loop
		while (iterator1.hasNext() && iterator2.hasNext()) {
			Integer start = (Integer) iterator1.next();
			Integer end = (Integer) iterator2.next();
			for (int k = ii; k < start - 1; k++) {
				final_res += parts.get(k) + " ";
			}
			final_res += removeBrackets(reps_start.get(start).toString()) + " ";
			ii = end - 1;
		}

		if (ii < parts.size()) {
			for (int h = ii; h < parts.size(); h++) {
				final_res += parts.get(h) + " ";
			}
		}
		if (final_res.endsWith(" . ")) {
			final_res = final_res.substring(0, final_res.length() - 3) + ".";
		}
		if (final_res.startsWith(" ")) {
			final_res = final_res.substring(1, final_res.length());
		}
		return final_res;
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
		String para = "";
		Map<Integer, CorefChain> corefChains = document.get(CorefCoreAnnotations.CorefChainAnnotation.class);
		for (CoreMap sentence : document.get(CoreAnnotations.SentencesAnnotation.class)) {
			String modifiedSentence = "";
			if (corefChains != null) {
				modifiedSentence = replaceMentions(sentence, corefChains, document,
						sentence.get(CoreAnnotations.SentenceIndexAnnotation.class));
				para += " " + modifiedSentence;
			}
		}
		if (para.startsWith(" ")) {
			para = para.substring(1, para.length());
		}
		return para;
	}
}
