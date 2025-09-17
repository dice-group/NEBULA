package org.dice_research.coref;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;

import org.json.JSONObject;

/**
 * This class can be used to run coreference resolution on a file. It creates a
 * parallel writing thread that appends the results to file as a jsonl file and
 * other parallel "producer threads" that run the coreference resolution as a
 * parallel stream.
 */
public class CorefResolutionFile extends CoreferenceResolution {

	// The JSONL results file path
	private String destinationPath;

	// The writing queue
	private BlockingQueue<String> queue;

	/**
	 * Constructor. Initializes class-level attributes.
	 * 
	 * @param destinationPath
	 */
	public CorefResolutionFile(String destinationPath) {
		super();
		queue = new LinkedBlockingQueue<String>();
		this.destinationPath = destinationPath;
	}

	/**
	 * Creates a thread on an infinite loop responsible for writing the results to
	 * file until an endSignal is received.
	 * 
	 * @param endSignal String to signal the thread to stop
	 * @return
	 */
	public Thread createAndRunWritingThread(String endSignal) {
		Thread consumerThread = new Thread(() -> {
			try (FileWriter fileWriter = new FileWriter(this.destinationPath, true)) {
				while (true) {
					String message = queue.take();
					if (message.equals(endSignal)) {
						break;
					}
					fileWriter.write(message + "\n");
				}
			} catch (IOException | InterruptedException e) {
				e.printStackTrace();
			}
		});
		consumerThread.start();
		return consumerThread;
	}

	/**
	 * 
	 * @return Set with all the ids it has processed before
	 */
	private Set<String> getProcessedIDs() {
		Set<String> ids = new HashSet<String>();
		try (BufferedReader br = new BufferedReader(new FileReader(this.destinationPath))) {
			String line;
			while ((line = br.readLine()) != null) {
				JSONObject result = new JSONObject(line);
				ids.add(result.getString("id"));
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
		return ids;
	}

	/**
	 * Reads JSONL file, and writes results to file
	 * 
	 * @param input Path to JSONL file
	 * @throws InterruptedException
	 */
	public void handleJSONLFile(String input) throws InterruptedException {

		// get ids that have been processed already
		Set<String> ids = getProcessedIDs();
		System.out.println("Processed ids: "+ids);

		// start writing thread
		String endSignal = "stop";
		Thread writingThread = createAndRunWritingThread(endSignal);

		// thread safe progress
		AtomicInteger progress = new AtomicInteger();

		// load file to memory and process each line
		try (Stream<String> lines = Files.lines(Path.of(input))) {
			lines.parallel().forEach(textForCrR -> {
				try {
					System.out.println("Processed " + progress.incrementAndGet());
					JSONObject json = getJson(textForCrR);
					String id = json.getString("article_id");

					// skip if we've already processed this
					if (ids.contains(id)) {
						return;
					}
					String accutal = generateCrR(json.getString("article_text"));
					JSONObject result = new JSONObject();
					result.append("id", id);
					result.append("coreferenced_result", accutal);
					queue.put(result.toString());
				} catch (Exception e) {
					e.printStackTrace();
					// just skip the iteration if anything goes wrong
					return;
				}
			});
		} catch (IOException e) {
			e.printStackTrace();
		} finally {
			// send endSignal to stop the thread
			queue.put(endSignal);
		}

		// wait for the thread to finish
		writingThread.join();
	}

	public static void main(String[] args) throws InterruptedException {
		CorefResolutionFile coref = new CorefResolutionFile(args[0]);
		coref.handleJSONLFile(args[1]);
	}
}
