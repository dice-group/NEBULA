package org.dice_research.coref;

import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;

import org.json.JSONObject;


public class CorefResolutionFile extends CoreferenceResolution {

	private String destinationPath;
	private BlockingQueue<String> queue;

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
	 * Reads JSONL file, and writes results to file
	 * 
	 * @param input Path to JSONL file
	 * @throws InterruptedException
	 */
	public void handleJSONLFile(String input) throws InterruptedException {

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
					String accutal = generateCrR(json.getString("article_text"));
					String print = json.getString("article_id") + ", " + accutal;
					queue.put(print);
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

}
