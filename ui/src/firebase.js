import { initializeApp } from "firebase/app";
import { 
  getFirestore, 
  collection, 
  getDocs, 
  addDoc, 
  deleteDoc, 
  doc, 
  query, 
  orderBy,
  onSnapshot 
} from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyAXiS0WN2u5W3RnPiEjTKvJEj_ZgzlmTnc",
  authDomain: "dnax-64b1f.firebaseapp.com",
  projectId: "dnax-64b1f",
  storageBucket: "dnax-64b1f.firebasestorage.app",
  messagingSenderId: "233724153587",
  appId: "1:233724153587:web:65170631d00538766ff186",
  measurementId: "G-LGPK9D7JZ3"
};

// Initialize Firebase App & Cloud Firestore
const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);

const COLLECTION_NAME = "dnax_sequences";

/**
 * Fetch all stored sequences from Cloud Firestore ordered by creation date
 */
export async function getCloudSequences() {
  try {
    const colRef = collection(db, COLLECTION_NAME);
    const q = query(colRef, orderBy("created_at", "desc"));
    const snapshot = await getDocs(q);
    return snapshot.docs.map((docSnap, idx) => ({
      id: docSnap.id,
      ...docSnap.data()
    }));
  } catch (error) {
    console.error("Firestore getCloudSequences error:", error);
    return [];
  }
}

/**
 * Save a new synthetic construct document to Cloud Firestore
 */
export async function saveCloudSequence(seqData) {
  try {
    const colRef = collection(db, COLLECTION_NAME);
    const docData = {
      name: seqData.name || `DNAx_Construct_${Date.now().toString().slice(-4)}`,
      mode: seqData.mode || "linear",
      length: parseInt(seqData.length) || seqData.payload?.length || 500,
      gc_pct: parseFloat(seqData.gc_pct) || 50.0,
      payload: seqData.payload || "",
      linear_seq: seqData.linear_seq || seqData.payload || "",
      primers: seqData.primers || null,
      probes: seqData.probes || [],
      notes: seqData.notes || "",
      created_at: new Date().toISOString().replace("T", " ").slice(0, 19)
    };
    const docRef = await addDoc(colRef, docData);
    return { success: true, id: docRef.id };
  } catch (error) {
    console.error("Firestore saveCloudSequence error:", error);
    return { success: false, error: error.message };
  }
}

/**
 * Delete a construct document from Cloud Firestore
 */
export async function deleteCloudSequence(docId) {
  try {
    const docRef = doc(db, COLLECTION_NAME, String(docId));
    await deleteDoc(docRef);
    return { success: true };
  } catch (error) {
    console.error("Firestore deleteCloudSequence error:", error);
    return { success: false, error: error.message };
  }
}

/**
 * Real-time subscription listener for cloud database changes
 */
export function subscribeCloudSequences(callback) {
  try {
    const colRef = collection(db, COLLECTION_NAME);
    const q = query(colRef, orderBy("created_at", "desc"));
    return onSnapshot(q, (snapshot) => {
      const seqs = snapshot.docs.map((docSnap) => ({
        id: docSnap.id,
        ...docSnap.data()
      }));
      callback(seqs);
    });
  } catch (error) {
    console.error("Firestore subscribe error:", error);
    return () => {};
  }
}
