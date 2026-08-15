import express from 'express'
import supabase from '@supabase/supabase-js';
import {authMiddleware} from '../middleware/authMiddleware.js'
i

const router = express.Router()

export const signup = router.post('/signup', async (_req, res) => {
   try {
     const {email,password} = _req.body;
 
     if(!email || !password){
         return res.status(400).json({error:"Email and Password required"})
     }
 
     const { data, error } = await supabase.auth.signUp({email,password})
     
     if(error){
        console.log(`Error while signup: ${error}`)
     }

     return res.status(201).json({user: data.user})
   } catch (error) {
        console.error(error)
   }
})


export const login =router.post('/login', async (_req, res) => {
    const { email, password } = _req.body;

    if(!email || !password){
        return res.status(400).json({error:"Email and Password required"})
    }

    const { data, error } = await supabase.auth.signInWithPassword({email,password})

     if(error){
        console.log(`Error while login: ${error}`)
        return res.status(400).send(`Sorry! user can't login`);
     }

    return res.status(200).json({
        access_token: data.session.access_token,
        refresh_token: data.session.refresh_token
    });
})


export const logout = router.post('/logout',authMiddleware, async (_req, res) => {
    const { error } = await supabase.auth.signOut();
    
    if(error){
        console.log(`Error while signout: ${error}`)
     }
     return res.status(204).send();
});


